"""
Content Pre-Generation Script

Generates initial content library for all concepts to reduce runtime AI costs.
Run this script once per course to populate the content library.

Usage:
    python -m backend.scripts.pregenerate_content --course latin-grammar --concepts all
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import config
from backend.app.agent import generate_content
from backend.app.content_cache import cache_content, init_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


LEARNING_STYLES = ['visual', 'reading', 'dialogue', 'kinesthetic']


def generate_explanation(concept_id: str, learning_style: str, course_id: str = "latin-grammar") -> Dict[str, Any]:
    """
    Generate an initial explanation for a concept in a specific learning style.

    Args:
        concept_id: Concept identifier
        learning_style: Learning style to generate for
        course_id: Course identifier

    Returns:
        Generated explanation content
    """
    logger.info(f"Generating {learning_style} explanation for {concept_id}...")

    try:
        # Create a temporary learner ID for generation
        temp_learner_id = f"pregen-{learning_style}-{datetime.now().timestamp()}"

        # Generate content using existing agent
        # Note: This uses the AI agent's generate_content function
        result = generate_content(
            learner_id=temp_learner_id,
            stage="start",
            correctness=None,
            confidence=None
        )

        if result.get("success"):
            content = result.get("content")
            logger.info(f"✓ Generated {learning_style} explanation for {concept_id}")
            return content
        else:
            logger.error(f"✗ Failed to generate {learning_style} explanation for {concept_id}")
            return None

    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        return None


def save_pregenerated_content(
    course_id: str,
    concept_id: str,
    content_type: str,
    learning_style: str,
    content: Dict[str, Any]
):
    """
    Save pre-generated content to the content library.

    Args:
        course_id: Course identifier
        concept_id: Concept identifier
        content_type: Type of content
        learning_style: Learning style
        content: Content to save
    """
    try:
        concept_dir = config.get_concept_dir(concept_id, course_id)
        content_library = concept_dir / "content-library"

        if content_type == "explanation":
            output_dir = content_library / "explanations"
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / f"{learning_style}.json"

            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "content_type": "explanation",
                    "learning_style": learning_style,
                    "concept_id": concept_id,
                    "generated_at": datetime.now().isoformat(),
                    "generated_by": "pre-generation-script",
                    "content": content
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Saved to {output_file}")

            # Also cache in database for unified access
            cache_content(
                course_id=course_id,
                concept_id=concept_id,
                content_type="explanation",
                tags={
                    "stage": "start",
                    "learning_style": learning_style
                },
                content_data=content,
                generated_by="pre-gen"
            )

    except Exception as e:
        logger.error(f"Error saving pre-generated content: {e}")
        raise


def pregenerate_concept(concept_id: str, course_id: str = "latin-grammar"):
    """
    Pre-generate all content for a single concept.

    Args:
        concept_id: Concept identifier
        course_id: Course identifier
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Pre-generating content for {concept_id}")
    logger.info(f"{'='*60}")

    # Generate explanation for each learning style
    for learning_style in LEARNING_STYLES:
        try:
            content = generate_explanation(concept_id, learning_style, course_id)

            if content:
                save_pregenerated_content(
                    course_id=course_id,
                    concept_id=concept_id,
                    content_type="explanation",
                    learning_style=learning_style,
                    content=content
                )
            else:
                logger.warning(f"Skipping save for {learning_style} - no content generated")

        except Exception as e:
            logger.error(f"Error pre-generating {learning_style} for {concept_id}: {e}")
            continue

    logger.info(f"✓ Completed pre-generation for {concept_id}\n")


def main():
    """Main entry point for pre-generation script."""
    parser = argparse.ArgumentParser(description='Pre-generate content for course concepts')
    parser.add_argument('--course', type=str, default='latin-grammar',
                        help='Course ID to generate content for')
    parser.add_argument('--concepts', type=str, default='all',
                        help='Comma-separated concept IDs or "all"')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be generated without actually generating')

    args = parser.parse_args()

    # Initialize cache database
    logger.info("Initializing content cache database...")
    init_database()

    # Determine which concepts to process
    if args.concepts == 'all':
        # Find all concepts in the course
        course_dir = config.get_course_dir(args.course)
        concept_dirs = sorted([d for d in course_dir.iterdir()
                               if d.is_dir() and d.name.startswith('concept-')])
        concepts = [d.name for d in concept_dirs]
    else:
        concepts = [c.strip() for c in args.concepts.split(',')]

    logger.info(f"\nPre-generation plan:")
    logger.info(f"  Course: {args.course}")
    logger.info(f"  Concepts: {', '.join(concepts)}")
    logger.info(f"  Learning styles: {', '.join(LEARNING_STYLES)}")
    logger.info(f"  Total items to generate: {len(concepts) * len(LEARNING_STYLES)}")

    if args.dry_run:
        logger.info("\n[DRY RUN] No content will be generated")
        return

    # Confirm before proceeding
    response = input("\nThis will make AI API calls and incur costs. Continue? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Cancelled by user")
        return

    # Process each concept
    start_time = datetime.now()

    for concept_id in concepts:
        pregenerate_concept(concept_id, args.course)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60

    logger.info(f"\n{'='*60}")
    logger.info(f"Pre-generation complete!")
    logger.info(f"  Generated content for {len(concepts)} concepts")
    logger.info(f"  Total items: {len(concepts) * len(LEARNING_STYLES)}")
    logger.info(f"  Duration: {duration:.2f} minutes")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
