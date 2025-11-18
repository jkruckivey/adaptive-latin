from fastapi import APIRouter, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
import json
import io

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

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)

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

@router.get("/courses/{course_id}", response_model=CourseMetadata)
async def get_course(course_id: str):
    """
    Get metadata for a specific course.
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
