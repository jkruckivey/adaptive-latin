"""
Migration script to restructure Fundamentals of Excel and Analytics
from 2 modules/5 concepts to proper 7-module structure.

This matches the authoring plan from AUTHORING-TOOL-COPY-PASTE.md
"""

import json
import shutil
from pathlib import Path

# Define the course directory
COURSE_DIR = Path(__file__).parent.parent / "resource-bank" / "user-courses" / "fundamentals-of-excel-and-analytics"

# Define the new 7-module structure based on authoring plan
NEW_STRUCTURE = [
    {
        "id": "module-001",
        "title": "Bridge-In & Pre-Assessment",
        "module_learning_outcomes": [
            "Assess current comfort level with mathematical concepts required for MBA analytics coursework",
            "Identify areas requiring focused attention during the course",
            "Recognize how functions model business relationships through concrete examples"
        ]
    },
    {
        "id": "module-002",
        "title": "Linear Functions",
        "module_learning_outcomes": [
            "Define functions and identify input-output relationships",
            "Interpret the slope (m) in y = mx + b as variable cost or rate of change in business contexts",
            "Interpret the intercept (b) in y = mx + b as fixed cost or baseline value in business contexts",
            "Graph linear functions using Excel and identify how changing m and b affects the line",
            "Apply linear functions to model cost, revenue, and break-even scenarios"
        ]
    },
    {
        "id": "module-003",
        "title": "Quadratic Functions",
        "module_learning_outcomes": [
            "Identify quadratic functions in the form y = ax² + bx + c",
            "Interpret the coefficient 'a' to determine parabola direction (opens up/down) and width (narrow/wide)",
            "Calculate vertex coordinates to find maximum or minimum values in business optimization problems",
            "Apply quadratic functions to model profit maximization and revenue optimization scenarios",
            "Use Excel to graph parabolas and identify optimal business decisions"
        ]
    },
    {
        "id": "module-004",
        "title": "Functions Practice & Assessment",
        "module_learning_outcomes": [
            "Distinguish between linear and quadratic business scenarios",
            "Select the appropriate function type (linear or quadratic) based on problem characteristics",
            "Build Excel models combining cost, revenue, and profit functions",
            "Communicate quantitative findings to business stakeholders through written analysis",
            "Evaluate pricing and production decisions using function-based models"
        ]
    },
    {
        "id": "module-005",
        "title": "Measures of Central Tendency & Dispersion",
        "module_learning_outcomes": [
            "Calculate mean, median, and mode using Excel functions (AVERAGE, MEDIAN, MODE.SNGL)",
            "Interpret measures of central tendency to summarize business datasets",
            "Calculate variance and standard deviation using Excel functions (VAR.S, STDEV.S)",
            "Interpret standard deviation to assess risk, volatility, and consistency in business metrics",
            "Select appropriate measures of central tendency and dispersion based on data characteristics"
        ]
    },
    {
        "id": "module-006",
        "title": "Relationships Between Variables",
        "module_learning_outcomes": [
            "Calculate correlation coefficients using Excel's CORREL function",
            "Interpret correlation coefficient strength and direction",
            "Create and interpret scatter plots to visualize relationships",
            "Distinguish between correlation and causation",
            "Evaluate whether correlations suggest actionable business insights"
        ]
    },
    {
        "id": "module-007",
        "title": "Statistics Assessment",
        "module_learning_outcomes": [
            "Apply descriptive statistics to analyze real business datasets",
            "Calculate and interpret correlation coefficients in business contexts",
            "Synthesize statistical findings into data-driven business recommendations",
            "Communicate quantitative analysis to non-technical stakeholders",
            "Evaluate data quality and limitations when making business decisions"
        ]
    }
]

def backup_existing_structure():
    """Create a backup of the existing structure."""
    backup_dir = COURSE_DIR.parent / "fundamentals-of-excel-and-analytics-backup"

    if backup_dir.exists():
        print(f"Backup already exists at {backup_dir}")
        return

    print(f"Creating backup at {backup_dir}")
    shutil.copytree(COURSE_DIR, backup_dir)
    print("Backup created successfully")

def read_existing_concepts():
    """Read the existing 5 concepts from the current 2-module structure."""
    concepts = []

    # Read from module-001
    module_001_dir = COURSE_DIR / "module-001"
    if module_001_dir.exists():
        for concept_dir in sorted(module_001_dir.glob("concept-*")):
            metadata_file = concept_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    concepts.append({
                        "old_path": concept_dir,
                        "metadata": json.load(f)
                    })

    # Read from module-002
    module_002_dir = COURSE_DIR / "module-002"
    if module_002_dir.exists():
        for concept_dir in sorted(module_002_dir.glob("concept-*")):
            metadata_file = concept_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    concepts.append({
                        "old_path": concept_dir,
                        "metadata": json.load(f)
                    })

    return concepts

def create_new_structure():
    """Create the new 7-module structure."""

    # Read existing concepts
    existing_concepts = read_existing_concepts()
    print(f"\nFound {len(existing_concepts)} existing concepts")

    # Delete old module directories
    for old_module in ["module-001", "module-002"]:
        old_module_dir = COURSE_DIR / old_module
        if old_module_dir.exists():
            print(f"Removing old {old_module}")
            shutil.rmtree(old_module_dir)

    # Create new 7-module structure
    for module_info in NEW_STRUCTURE:
        module_dir = COURSE_DIR / module_info["id"]
        module_dir.mkdir(parents=True, exist_ok=True)

        # Create module metadata
        module_metadata = {
            "id": module_info["id"],
            "title": module_info["title"],
            "module_learning_outcomes": module_info["module_learning_outcomes"]
        }

        module_metadata_file = module_dir / "metadata.json"
        with open(module_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(module_metadata, f, indent=2, ensure_ascii=False)

        print(f"Created {module_info['id']}: {module_info['title']}")

        # For now, create a single placeholder concept in each module
        # (In a full implementation, you'd map existing content to appropriate modules)
        concept_dir = module_dir / "concept-001"
        concept_dir.mkdir(parents=True, exist_ok=True)

        # Create concept metadata
        concept_metadata = {
            "concept_id": "concept-001",
            "title": module_info["title"],
            "learning_objectives": module_info["module_learning_outcomes"],
            "prerequisites": []
        }

        concept_metadata_file = concept_dir / "metadata.json"
        with open(concept_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(concept_metadata, f, indent=2, ensure_ascii=False)

        # Create resources directory structure
        resources_dir = concept_dir / "resources"
        resources_dir.mkdir(parents=True, exist_ok=True)

        # Create placeholder files
        (resources_dir / "text-explainer.md").write_text(
            f"# {module_info['title']}\n\nContent to be added.",
            encoding='utf-8'
        )

        examples_file = resources_dir / "examples.json"
        with open(examples_file, 'w', encoding='utf-8') as f:
            json.dump({"examples": []}, f, indent=2, ensure_ascii=False)

        # Create assessments directory
        assessments_dir = concept_dir / "assessments"
        assessments_dir.mkdir(parents=True, exist_ok=True)

    print("\nSuccessfully created 7-module structure")

def main():
    print("="*60)
    print("Excel Course Migration: 2 modules -> 7 modules")
    print("="*60)

    # Backup
    backup_existing_structure()

    # Create new structure
    create_new_structure()

    print("\n" + "="*60)
    print("Migration complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Copy content from backup into appropriate new modules")
    print("2. Update learner progress data if needed")
    print("3. Test the course in the frontend")

if __name__ == "__main__":
    main()
