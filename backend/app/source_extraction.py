"""
Source Extraction Service

Handles extraction of metadata and content from external learning resources.
Uses a hybrid approach: extract lightweight metadata immediately, full content on-demand.
"""

import logging
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


def detect_source_type(url: str) -> str:
    """
    Detect the type of source from URL.

    Args:
        url: Source URL

    Returns:
        Source type: video, website, pdf, image, audio
    """
    url_lower = url.lower()

    # Video platforms
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'video'
    if 'vimeo.com' in url_lower:
        return 'video'

    # File extensions
    if url_lower.endswith('.pdf'):
        return 'pdf'
    if url_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp')):
        return 'image'
    if url_lower.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
        return 'audio'
    if url_lower.endswith(('.mp4', '.mov', '.avi', '.webm')):
        return 'video'

    # Default to website
    return 'website'


def extract_youtube_metadata(url: str) -> Dict[str, Any]:
    """
    Extract metadata from YouTube video URL.

    Args:
        url: YouTube video URL

    Returns:
        Metadata dictionary with title, description, duration, etc.
    """
    try:
        # Extract video ID
        video_id = None
        if 'youtube.com' in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            video_id = query_params.get('v', [None])[0]
        elif 'youtu.be' in url:
            video_id = urlparse(url).path.split('/')[-1]

        if not video_id:
            raise ValueError("Could not extract YouTube video ID")

        # Use oembed API for basic metadata (no API key needed)
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            "title": data.get("title", "YouTube Video"),
            "description": f"Video by {data.get('author_name', 'Unknown')}",
            "author": data.get("author_name"),
            "thumbnail_url": data.get("thumbnail_url"),
            "video_id": video_id,
            "content_preview": f"YouTube video: {data.get('title', 'Untitled')}"
        }

    except Exception as e:
        logger.error(f"Error extracting YouTube metadata: {e}")
        return {
            "title": "YouTube Video",
            "description": "Video content",
            "content_preview": url
        }


def extract_website_metadata(url: str) -> Dict[str, Any]:
    """
    Extract metadata from website URL.

    Args:
        url: Website URL

    Returns:
        Metadata dictionary with title, description, preview text
    """
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; EducationalBot/1.0)'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        html = response.text

        # Extract title from <title> tag
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Website"

        # Extract meta description
        desc_match = re.search(
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
            html,
            re.IGNORECASE
        )
        if not desc_match:
            desc_match = re.search(
                r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']description["\']',
                html,
                re.IGNORECASE
            )
        description = desc_match.group(1).strip() if desc_match else ""

        # Extract text preview (first 500 chars of visible text)
        # Remove script and style tags
        text_content = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text_content = re.sub(r'<[^>]+>', '', text_content)
        # Clean up whitespace
        text_content = ' '.join(text_content.split())
        content_preview = text_content[:500] + "..." if len(text_content) > 500 else text_content

        return {
            "title": title[:200],  # Limit title length
            "description": description[:500] if description else content_preview[:200],
            "content_preview": content_preview,
            "url": url
        }

    except Exception as e:
        logger.error(f"Error extracting website metadata: {e}")
        return {
            "title": urlparse(url).netloc or "Website",
            "description": "External website content",
            "content_preview": url
        }


def extract_pdf_metadata(url: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF URL.

    Args:
        url: PDF file URL

    Returns:
        Metadata dictionary
    """
    try:
        # HEAD request to get file info without downloading
        response = requests.head(url, timeout=10, allow_redirects=True)
        response.raise_for_status()

        file_size = response.headers.get('Content-Length', 'Unknown')
        if file_size != 'Unknown':
            file_size_mb = int(file_size) / (1024 * 1024)
            file_size = f"{file_size_mb:.2f} MB"

        # Extract filename from URL
        filename = urlparse(url).path.split('/')[-1]

        return {
            "title": filename or "PDF Document",
            "description": f"PDF document ({file_size})",
            "file_size": file_size,
            "filename": filename,
            "content_preview": f"PDF: {filename}"
        }

    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {e}")
        return {
            "title": "PDF Document",
            "description": "PDF file",
            "content_preview": url
        }


def extract_source_metadata(url: str, source_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract metadata from a source URL (lightweight extraction for preview).

    Args:
        url: Source URL
        source_type: Optional explicit source type, otherwise auto-detected

    Returns:
        Dictionary with metadata including:
        - type: Source type
        - url: Original URL
        - title: Extracted title
        - description: Brief description
        - metadata: Type-specific metadata
        - status: 'ready' or 'error'
    """
    try:
        # Detect or use provided source type
        if not source_type:
            source_type = detect_source_type(url)

        # Extract type-specific metadata
        if source_type == 'video' and ('youtube.com' in url or 'youtu.be' in url):
            metadata = extract_youtube_metadata(url)
        elif source_type == 'pdf':
            metadata = extract_pdf_metadata(url)
        elif source_type == 'website':
            metadata = extract_website_metadata(url)
        else:
            # Generic metadata for images, audio, other files
            metadata = {
                "title": urlparse(url).path.split('/')[-1] or source_type.capitalize(),
                "description": f"{source_type.capitalize()} resource",
                "content_preview": url
            }

        return {
            "type": source_type,
            "url": url,
            "title": metadata.get("title", "Untitled"),
            "description": metadata.get("description", ""),
            "metadata": metadata,
            "added_at": datetime.now().isoformat(),
            "status": "ready"
        }

    except Exception as e:
        logger.error(f"Error extracting metadata from {url}: {e}")
        return {
            "type": source_type or "unknown",
            "url": url,
            "title": "Source",
            "description": "External resource",
            "metadata": {},
            "added_at": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e)
        }


def load_full_source_content(url: str, source_type: str) -> Dict[str, Any]:
    """
    Load full content from a source (on-demand, not stored).

    This is called by the AI agent when it needs the actual content.

    Args:
        url: Source URL
        source_type: Source type

    Returns:
        Dictionary with full content
    """
    try:
        if source_type == 'website':
            # Fetch and extract full text
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; EducationalBot/1.0)'
            }
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()

            html = response.text

            # Remove script and style tags
            text_content = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
            # Remove HTML tags
            text_content = re.sub(r'<[^>]+>', ' ', text_content)
            # Clean up whitespace
            text_content = ' '.join(text_content.split())

            return {
                "success": True,
                "content": text_content,
                "content_type": "text",
                "length": len(text_content)
            }

        elif source_type == 'pdf':
            # For PDFs, we'd need PyPDF2 or similar
            # For now, return placeholder
            return {
                "success": False,
                "error": "PDF content extraction requires additional setup. Please install PyPDF2 or pdfplumber.",
                "content_type": "pdf"
            }

        else:
            return {
                "success": False,
                "error": f"Full content loading not yet implemented for {source_type}",
                "content_type": source_type
            }

    except Exception as e:
        logger.error(f"Error loading full content from {url}: {e}")
        return {
            "success": False,
            "error": str(e),
            "content_type": source_type
        }
