"""
Migrate Excel course from flat structure to module-based structure.
"""

import json
import shutil
from pathlib import Path

# Course path
course_path = Path("../resource-bank/user-courses/fundamentals-of-excel-and-analytics")

# Define module structure
modules = {
    "module-001": {
        "title": "Functions and Modeling",
        "module_learning_outcomes": [
            "Analyze business scenarios using linear and quadratic function models",
            "Model business scenarios using Excel formulas and visualizations"
        ],
        "concepts": ["concept-001", "concept-002", "concept-003"]
    },
    "module-002": {
        "title": "Statistical Analysis",
        "module_learning_outcomes": [
            "Interpret descriptive statistics to support data-driven business decisions",
            "Evaluate relationships between variables using correlation analysis"
        ],
        "concepts": ["concept-004", "concept-005"]
    }
}

def migrate_course():
    """Migrate course from flat to module structure."""

    print(f"Migrating course: {course_path}")

    # Create module directories and move concepts
    for module_id, module_data in modules.items():
        module_dir = course_path / module_id
        print(f"\nCreating module: {module_id} - {module_data['title']}")
        module_dir.mkdir(exist_ok=True)

        # Create module metadata
        module_metadata = {
            "id": module_id,
            "title": module_data["title"],
            "module_learning_outcomes": module_data["module_learning_outcomes"]
        }

        metadata_path = module_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(module_metadata, f, indent=2, ensure_ascii=False)

        print(f"Created module metadata: {metadata_path}")

        # Move concepts into module
        for concept_id in module_data["concepts"]:
            old_concept_path = course_path / concept_id
            new_concept_path = module_dir / concept_id

            if old_concept_path.exists() and not new_concept_path.exists():
                shutil.move(str(old_concept_path), str(new_concept_path))
                print(f"Moved {concept_id} into {module_id}")
            elif new_concept_path.exists():
                print(f"{concept_id} already in {module_id}")
            else:
                print(f"WARNING: {concept_id} not found")

    print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate_course()
