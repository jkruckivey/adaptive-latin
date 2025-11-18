"""
Common Cartridge (.imscc) Parser

Parses IMS Common Cartridge exports from Canvas, Moodle, Blackboard, etc.
Extracts course structure, modules, content, and learning outcomes.
"""

import zipfile
import xml.etree.ElementTree as ET
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import shutil

logger = logging.getLogger(__name__)

# Common Cartridge XML namespaces
NAMESPACES = {
    'imscc': 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1',
    'imsmd': 'http://ltsc.ieee.org/xsd/imsmd_v1p2',
    'lom': 'http://ltsc.ieee.org/xsd/LOM',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


def strip_html(html_content: str) -> str:
    """Remove HTML tags and return plain text."""
    if not html_content:
        return ""

    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', html_content)
    # Clean up whitespace
    clean = re.sub(r'\s+', ' ', clean)
    # Decode common HTML entities
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return clean.strip()


def extract_text_from_element(element: Optional[ET.Element], namespaces: Dict = None) -> str:
    """Extract text content from an XML element."""
    if element is None:
        return ""

    text = element.text or ""
    # Also get text from all child elements
    for child in element:
        child_text = extract_text_from_element(child, namespaces)
        if child_text:
            text += " " + child_text

    return text.strip()


class CommonCartridgeParser:
    """Parser for IMS Common Cartridge files."""

    def __init__(self, file_path: Path):
        """
        Initialize parser with path to .imscc file.

        Args:
            file_path: Path to the .imscc (ZIP) file
        """
        self.file_path = file_path
        self.temp_dir = None
        self.manifest = None
        self.resources = {}
        self.items = {}

    def parse(self) -> Dict[str, Any]:
        """
        Parse the Common Cartridge file and extract course data.

        Returns:
            Dictionary with course structure and content
        """
        try:
            # Create temp directory for extraction
            self.temp_dir = Path(tempfile.mkdtemp())
            logger.info(f"Extracting cartridge to {self.temp_dir}")

            # Extract the ZIP file
            with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)

            # Parse the manifest
            manifest_path = self.temp_dir / "imsmanifest.xml"
            if not manifest_path.exists():
                raise ValueError("Invalid Common Cartridge: imsmanifest.xml not found")

            tree = ET.parse(manifest_path)
            self.manifest = tree.getroot()

            # Extract course metadata
            course_data = self._extract_course_metadata()

            # Extract modules and content
            modules = self._extract_modules()
            course_data['modules'] = modules

            logger.info(f"Successfully parsed cartridge: {course_data.get('title', 'Unknown')}")
            logger.info(f"Extracted {len(modules)} modules")

            return course_data

        except Exception as e:
            logger.error(f"Error parsing Common Cartridge: {e}")
            raise
        finally:
            # Cleanup temp directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

    def _extract_course_metadata(self) -> Dict[str, Any]:
        """Extract course-level metadata from manifest."""
        metadata = {
            'title': 'Imported Course',
            'description': '',
            'domain': 'Other',
            'taxonomy': 'blooms',
            'courseLearningOutcomes': [],
            'targetAudience': ''
        }

        # Try to find metadata in manifest
        ns = {'imscc': NAMESPACES['imscc']}

        # Get course title
        title_elem = self.manifest.find('.//imscc:metadata/imscc:lom/imscc:general/imscc:title/imscc:string', ns)
        if title_elem is not None and title_elem.text:
            metadata['title'] = title_elem.text
        else:
            # Fallback: try to get from organization title
            org_title = self.manifest.find('.//imscc:organizations/imscc:organization/imscc:title', ns)
            if org_title is not None and org_title.text:
                metadata['title'] = org_title.text

        # Get course description
        desc_elem = self.manifest.find('.//imscc:metadata/imscc:lom/imscc:general/imscc:description/imscc:string', ns)
        if desc_elem is not None and desc_elem.text:
            metadata['description'] = desc_elem.text

        logger.info(f"Extracted course metadata: {metadata['title']}")

        return metadata

    def _extract_modules(self) -> List[Dict[str, Any]]:
        """Extract module structure from the cartridge."""
        modules = []

        ns = {'imscc': NAMESPACES['imscc']}

        # Find the organization (course structure)
        organization = self.manifest.find('.//imscc:organizations/imscc:organization', ns)
        if organization is None:
            logger.warning("No organization found in manifest")
            return modules

        # Get top-level items (typically modules/weeks)
        module_items = organization.findall('./imscc:item', ns)

        for idx, item in enumerate(module_items, 1):
            module_data = self._parse_module_item(item, idx, ns)
            if module_data:
                modules.append(module_data)

        return modules

    def _parse_module_item(self, item: ET.Element, module_num: int, ns: Dict) -> Optional[Dict[str, Any]]:
        """Parse a single module item."""
        title_elem = item.find('./imscc:title', ns)
        title = title_elem.text if title_elem is not None and title_elem.text else f"Module {module_num}"

        logger.info(f"Parsing module: {title}")

        module_data = {
            'moduleId': f"module-{module_num:03d}",
            'title': title,
            'moduleLearningOutcomes': [],
            'concepts': []
        }

        # Get child items (pages, assignments, etc.)
        child_items = item.findall('./imscc:item', ns)

        for concept_idx, child_item in enumerate(child_items, 1):
            concept_data = self._parse_concept_item(child_item, concept_idx, ns)
            if concept_data:
                module_data['concepts'].append(concept_data)

        return module_data

    def _parse_concept_item(self, item: ET.Element, concept_num: int, ns: Dict) -> Optional[Dict[str, Any]]:
        """Parse a single concept/page item."""
        title_elem = item.find('./imscc:title', ns)
        title = title_elem.text if title_elem is not None and title_elem.text else f"Concept {concept_num}"

        # Get identifier reference (points to resource)
        identifier_ref = item.get('identifierref')

        concept_data = {
            'conceptId': f"concept-{concept_num:03d}",
            'title': title,
            'learningObjectives': [],
            'prerequisites': [],
            'teachingContent': '',
            'vocabulary': []
        }

        # Try to extract content from referenced resource
        if identifier_ref:
            content = self._extract_resource_content(identifier_ref, ns)
            if content:
                concept_data['teachingContent'] = content[:1000]  # Limit to first 1000 chars

        return concept_data

    def _extract_resource_content(self, identifier: str, ns: Dict) -> str:
        """Extract content from a resource by identifier."""
        # Find the resource in the manifest
        resource = self.manifest.find(f'.//imscc:resource[@identifier="{identifier}"]', ns)
        if resource is None:
            return ""

        # Get the href (file path)
        href = resource.get('href')
        if not href:
            return ""

        # Try to read the file
        file_path = self.temp_dir / href
        if not file_path.exists():
            logger.warning(f"Resource file not found: {href}")
            return ""

        try:
            # Read HTML content
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Strip HTML tags to get plain text
            plain_text = strip_html(html_content)
            return plain_text

        except Exception as e:
            logger.error(f"Error reading resource {href}: {e}")
            return ""


def parse_common_cartridge(file_path: Path) -> Dict[str, Any]:
    """
    Parse a Common Cartridge file and return course data.

    Args:
        file_path: Path to the .imscc file

    Returns:
        Dictionary with course structure suitable for the course creator wizard
    """
    parser = CommonCartridgeParser(file_path)
    return parser.parse()
