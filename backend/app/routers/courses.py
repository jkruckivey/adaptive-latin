from fastapi import APIRouter, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
import json
import io
from anthropic import Anthropic

from .. import config
from ..schemas import (
    CourseMetadata,
    CreateCourseRequest,
    ImportCourseRequest,
    CoursesListResponse,
    AddSourceRequest,
    SourceResponse,
    SourceContentResponse
)
from ..tools import (
    list_all_courses,
    load_course_metadata,
    delete_course,
    import_course_data,
    add_course_source,
    add_concept_source,
    delete_source_from_course,
    delete_source_from_concept,
    list_all_modules
)
from ..content_generators import (
    generate_learning_outcomes,
    generate_module_learning_outcomes,
    generate_concept_learning_objectives,
    generate_simulation_content
)
from ..cartridge_parser import parse_common_cartridge
from ..source_extraction import extract_text_from_url, extract_text_from_pdf
from ..dependency_analyzer import analyze_course_dependencies

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Anthropic client for AI generation
client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

@router.get("/courses", response_model=CoursesListResponse)
async def list_courses_endpoint():
    """
    List all available courses.
    """
    try:
        courses = list_all_courses()
        return {
            "courses": courses,
            "total": len(courses)
        }
    except Exception as e:
        logger.error(f"Error listing courses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list courses: {str(e)}"
        )

@router.post("/courses", status_code=status.HTTP_201_CREATED)
async def create_course(request: CreateCourseRequest):
    """
    Create a new course.
    """
    try:
        # Check if course already exists
        course_dir = config.RESOURCE_BANK_DIR / request.course_id
        if course_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Course '{request.course_id}' already exists"
            )

        # Create course directory
        course_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        metadata = request.dict()
        
        # Add timestamps
        from datetime import datetime
        now = datetime.now().isoformat()
        metadata["created_at"] = now
        metadata["updated_at"] = now
        
        # Save metadata
        metadata_file = course_dir / "course_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        # Create concepts directory
        (course_dir / "concepts").mkdir(exist_ok=True)
        
        # Create modules directory if modules provided
        if request.modules:
            modules_dir = course_dir / "modules"
            modules_dir.mkdir(exist_ok=True)
            
            # Save modules metadata
            modules_file = course_dir / "modules.json"
            with open(modules_file, "w", encoding="utf-8") as f:
                json.dump(request.modules, f, indent=2)
                
        logger.info(f"Created new course: {request.course_id}")
        
        return {
            "success": True,
            "course_id": request.course_id,
            "message": "Course created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course: {str(e)}"
        )

@router.get("/courses/{course_id}/analyze-dependencies")
async def analyze_dependencies_endpoint(course_id: str):
    """
    Analyze concept dependency structure for a course.

    Detects: circular dependencies, orphaned concepts, suggests optimal ordering,
    identifies bottleneck concepts, finds parallel learning paths, calculates complexity metrics
    """
    try:
        from pathlib import Path
        course = load_course_metadata(course_id)
        concepts = []

        # Try loading concepts from modules first (user-created courses)
        modules_data = list_all_modules(course_id)
        if isinstance(modules_data, dict) and modules_data.get('success') and modules_data.get('modules'):
            for module in modules_data['modules']:
                for concept_id in module.get('concepts', []):
                    try:
                        concept_path = Path(config.get_concept_dir(concept_id, course_id)) / "metadata.json"
                        if concept_path.exists():
                            with open(concept_path, 'r', encoding='utf-8') as f:
                                concept_data = json.load(f)
                                concepts.append(concept_data)
                    except Exception as e:
                        logger.warning(f"Failed to load concept {concept_id}: {e}")

        # If no modules, scan course directory for concept folders (built-in courses like latin-grammar)
        if not concepts:
            course_dir = Path(config.RESOURCE_BANK_DIR) / course_id
            if course_dir.exists():
                for concept_dir in sorted(course_dir.iterdir()):
                    if concept_dir.is_dir() and concept_dir.name.startswith('concept-'):
                        metadata_file = concept_dir / "metadata.json"
                        if metadata_file.exists():
                            try:
                                with open(metadata_file, 'r', encoding='utf-8') as f:
                                    concept_data = json.load(f)
                                    concepts.append(concept_data)
                            except Exception as e:
                                logger.warning(f"Failed to load {concept_dir.name}: {e}")

        if not concepts:
            return {"success": False, "error": "No concepts found for this course"}

        analysis = analyze_course_dependencies(course_id, concepts)

        return {
            "success": True,
            "course_id": course_id,
            "course_title": course.get('title', course_id),
            "analysis": analysis
        }
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course not found: {course_id}")
    except Exception as e:
        logger.error(f"Error analyzing dependencies for {course_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to analyze dependencies: {str(e)}")

@router.get("/courses/{course_id}")
async def get_course(course_id: str):
    """
    Get metadata for a specific course.
    Returns raw course metadata including onboarding_questions.
    """
    try:
        metadata = load_course_metadata(course_id)
        return metadata
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course not found: {course_id}"
        )
    except Exception as e:
        logger.error(f"Error getting course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course: {str(e)}"
        )

@router.delete("/courses/{course_id}")
async def delete_course_endpoint(course_id: str):
    """
    Delete a course and all its content.
    """
    try:
        success = delete_course(course_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course not found: {course_id}"
            )
            
        return {
            "success": True,
            "message": f"Course {course_id} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete course: {str(e)}"
        )

@router.post("/courses/import")
async def import_course(request: ImportCourseRequest):
    """
    Import a course from exported JSON data.
    """
    try:
        course_id = import_course_data(
            request.export_data, 
            request.new_course_id, 
            request.overwrite
        )
        
        return {
            "success": True,
            "course_id": course_id,
            "message": "Course imported successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error importing course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import course: {str(e)}"
        )

@router.get("/courses/{course_id}/export")
async def export_course(course_id: str):
    """
    Export a course to JSON format.
    """
    try:
        # Load all course data
        metadata = load_course_metadata(course_id)
        
        # Load modules if they exist
        try:
            modules = list_all_modules(course_id)
            metadata["modules"] = modules
        except:
            pass
            
        # Load concepts with their full content
        # This would be a more complex implementation to gather all files
        # For now, we'll just return the metadata which contains the structure
        
        return metadata
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course not found: {course_id}"
        )
    except Exception as e:
        logger.error(f"Error exporting course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export course: {str(e)}"
        )

@router.post("/courses/import-cartridge")
async def import_common_cartridge(
    file: UploadFile = File(...),
    course_id: str = Form(...),
    title: Optional[str] = Form(None)
):
    """
    Import a course from a Common Cartridge (IMSCC) file.
    """
    try:
        if not file.filename.endswith('.imscc'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a Common Cartridge (.imscc) file"
            )
            
        # Read file content
        content = await file.read()
        
        # Parse cartridge
        course_data = parse_common_cartridge(io.BytesIO(content))
        
        # Override ID and title if provided
        if course_id:
            course_data["course_id"] = course_id
        if title:
            course_data["title"] = title
            
        # Import the course
        imported_id = import_course_data(course_data, course_id, overwrite=True)
        
        return {
            "success": True,
            "course_id": imported_id,
            "message": f"Successfully imported course from {file.filename}",
            "stats": {
                "modules": len(course_data.get("modules", [])),
                "resources": len(course_data.get("resources", []))
            }
        }
        
    except Exception as e:
        logger.error(f"Error importing cartridge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import cartridge: {str(e)}"
        )

# Source Management Endpoints

@router.post("/courses/{course_id}/sources", response_model=SourceResponse)
async def add_course_source_endpoint(course_id: str, request: AddSourceRequest):
    """
    Add a source to a course.
    """
    try:
        source = add_course_source(course_id, request.dict())
        return source
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course not found: {course_id}"
        )
    except Exception as e:
        logger.error(f"Error adding source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add source: {str(e)}"
        )

@router.delete("/courses/{course_id}/sources/{source_id}")
async def delete_course_source_endpoint(course_id: str, source_id: str):
    """
    Delete a source from a course.
    """
    try:
        success = delete_source_from_course(course_id, source_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source not found: {source_id}"
            )
        return {"success": True, "message": "Source deleted"}
    except Exception as e:
        logger.error(f"Error deleting source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete source: {str(e)}"
        )

@router.post("/courses/{course_id}/concepts/{concept_id}/sources", response_model=SourceResponse)
async def add_concept_source_endpoint(course_id: str, concept_id: str, request: AddSourceRequest):
    """
    Add a source to a concept.
    """
    try:
        source = add_concept_source(course_id, concept_id, request.dict())
        return source
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course or concept not found"
        )
    except Exception as e:
        logger.error(f"Error adding source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add source: {str(e)}"
        )

@router.delete("/courses/{course_id}/concepts/{concept_id}/sources/{source_id}")
async def delete_concept_source_endpoint(course_id: str, concept_id: str, source_id: str):
    """
    Delete a source from a concept.
    """
    try:
        success = delete_source_from_concept(course_id, concept_id, source_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source not found: {source_id}"
            )
        return {"success": True, "message": "Source deleted"}
    except Exception as e:
        logger.error(f"Error deleting source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete source: {str(e)}"
        )

@router.post("/extract-content", response_model=SourceContentResponse)
async def extract_content(request: Request, body: dict):
    """
    Extract content from a URL or file.
    """
    try:
        url = body.get("url")
        file_path = body.get("file_path")
        
        if url:
            content = extract_text_from_url(url)
            return {
                "success": True,
                "content": content,
                "content_type": "url",
                "length": len(content)
            }
        elif file_path:
            # For now, only support PDF
            if file_path.lower().endswith(".pdf"):
                content = extract_text_from_pdf(file_path)
                return {
                    "success": True,
                    "content": content,
                    "content_type": "pdf",
                    "length": len(content)
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file type"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide url or file_path"
            )
            
    except Exception as e:
        logger.error(f"Error extracting content: {e}")
        return {
            "success": False,
            "error": str(e),
            "content_type": "unknown"
        }

# AI Generation Endpoints

@router.post("/generate/outcomes")
async def generate_outcomes(request: Request, body: dict):
    """
    Generate learning outcomes for a course.
    """
    try:
        topic = body.get("topic")
        level = body.get("level", "beginner")
        count = body.get("count", 5)
        
        outcomes = generate_learning_outcomes(topic, level, count)
        
        return {
            "success": True,
            "outcomes": outcomes
        }
    except Exception as e:
        logger.error(f"Error generating outcomes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate outcomes: {str(e)}"
        )

@router.post("/generate/module-outcomes")
async def generate_mod_outcomes(request: Request, body: dict):
    """
    Generate learning outcomes for a module.
    """
    try:
        course_title = body.get("course_title")
        module_title = body.get("module_title")
        count = body.get("count", 3)
        
        outcomes = generate_module_learning_outcomes(course_title, module_title, count)
        
        return {
            "success": True,
            "outcomes": outcomes
        }
    except Exception as e:
        logger.error(f"Error generating module outcomes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate outcomes: {str(e)}"
        )

@router.post("/generate/concept-objectives")
async def generate_conc_objectives(request: Request, body: dict):
    """
    Generate learning objectives for a concept.
    """
    try:
        course_title = body.get("course_title")
        module_title = body.get("module_title")
        concept_title = body.get("concept_title")
        count = body.get("count", 3)
        
        objectives = generate_concept_learning_objectives(course_title, module_title, concept_title, count)
        
        return {
            "success": True,
            "objectives": objectives
        }
    except Exception as e:
        logger.error(f"Error generating objectives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate objectives: {str(e)}"
        )

@router.post("/generate/simulation")
async def generate_sim(request: Request, body: dict):
    """
    Generate a simulation scenario.
    """
    try:
        concept = body.get("concept")
        context = body.get("context")
        
        simulation = generate_simulation_content(concept, context)
        
        return {
            "success": True,
            "simulation": simulation
        }
    except Exception as e:
        logger.error(f"Error generating simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate simulation: {str(e)}"
        )

# ========================================
# Additional AI Generation Endpoints
# (Added to match frontend API expectations)
# ========================================

@router.post("/generate-learning-outcomes")
async def generate_learning_outcomes_endpoint(request: Request, body: dict):
    """
    Generate learning outcomes with AI based on description and taxonomy.
    
    Expects:
    - description: Course/module/concept description
    - taxonomy: Taxonomy to use ('blooms', 'finks', 'qm')
    - level: Level of outcomes ('course', 'module', 'concept')
    - count: Number of outcomes to generate
    - existing_outcomes: Optional list of existing outcomes to avoid duplication
    """
    try:
        description = body.get("description")
        taxonomy = body.get("taxonomy", "blooms")
        level = body.get("level", "course")
        count = body.get("count", 5)
        existing_outcomes = body.get("existing_outcomes")
        
        if not description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Description is required"
            )
        
        outcomes = generate_learning_outcomes(
            description=description,
            taxonomy=taxonomy,
            level=level,
            count=count,
            existing_outcomes=existing_outcomes
        )
        
        return {
            "success": True,
            "outcomes": outcomes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating learning outcomes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning outcomes: {str(e)}"
        )


@router.post("/generate-module-learning-outcomes")
async def generate_module_outcomes_endpoint(request: Request, body: dict):
    """
    Generate module learning outcomes with AI.
    
    Expects:
    - module_title: Title of the module
    - course_title: Title of the parent course
    - course_learning_outcomes: List of course-level outcomes
    - domain: Subject domain
    - taxonomy: Taxonomy to use (default: 'blooms')
    """
    try:
        module_title = body.get("module_title")
        course_title = body.get("course_title")
        course_learning_outcomes = body.get("course_learning_outcomes", [])
        domain = body.get("domain", "general")
        taxonomy = body.get("taxonomy", "blooms")
        
        if not module_title or not course_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="module_title and course_title are required"
            )
        
        outcomes = generate_module_learning_outcomes(
            module_title=module_title,
            course_title=course_title,
            course_learning_outcomes=course_learning_outcomes,
            domain=domain,
            taxonomy=taxonomy
        )
        
        return {
            "success": True,
            "outcomes": outcomes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating module learning outcomes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate module outcomes: {str(e)}"
        )


@router.post("/generate-concept-learning-objectives")
async def generate_concept_objectives_endpoint(request: Request, body: dict):
    """
    Generate concept learning objectives with AI.
    
    Expects:
    - concept_title: Title of the concept
    - module_title: Title of the parent module
    - module_learning_outcomes: List of module-level outcomes
    - course_title: Title of the course
    - domain: Subject domain
    - taxonomy: Taxonomy to use (default: 'blooms')
    """
    try:
        concept_title = body.get("concept_title")
        module_title = body.get("module_title")
        module_learning_outcomes = body.get("module_learning_outcomes", [])
        course_title = body.get("course_title")
        domain = body.get("domain", "general")
        taxonomy = body.get("taxonomy", "blooms")
        
        if not concept_title or not module_title or not course_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="concept_title, module_title, and course_title are required"
            )
        
        objectives = generate_concept_learning_objectives(
            concept_title=concept_title,
            module_title=module_title,
            module_learning_outcomes=module_learning_outcomes,
            course_title=course_title,
            domain=domain,
            taxonomy=taxonomy
        )
        
        return {
            "success": True,
            "objectives": objectives
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating concept learning objectives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate concept objectives: {str(e)}"
        )


@router.post("/generate-assessments")
async def generate_assessments_endpoint(request: Request, body: dict):
    """
    Generate assessments based on a learning outcome.
    
    Expects:
    - learning_outcome: The learning outcome to create assessments for
    - taxonomy: Taxonomy used (default: 'blooms')
    - domain: Subject domain (default: 'general')
    - num_assessments: Number of assessments to generate (default: 3)
    """
    try:
        learning_outcome = body.get("learning_outcome")
        taxonomy = body.get("taxonomy", "blooms")
        domain = body.get("domain", "general")
        num_assessments = body.get("num_assessments", 3)
        
        if not learning_outcome:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="learning_outcome is required"
            )
        
        # Generate assessments using AI
        prompt = f"""Generate {num_assessments} assessment questions for this learning outcome:

Learning Outcome: {learning_outcome}
Domain: {domain}
Taxonomy: {taxonomy}

Create varied assessment types (multiple choice, short answer, scenario-based) that effectively measure achievement of this outcome.

Return a JSON array where each assessment has:
- "type": assessment type (e.g., "multiple-choice", "short-answer", "scenario")
- "question": the question text
- "options": array of options (for multiple choice)
- "correct_answer": the correct answer or answer key
- "explanation": why this assesses the outcome

Return ONLY the JSON array."""

        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        assessments = json.loads(response_text)
        
        return {
            "success": True,
            "assessments": assessments
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating assessments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate assessments: {str(e)}"
        )
