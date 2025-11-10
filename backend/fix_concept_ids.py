"""
Fix concept IDs to be unique across all modules.
Changes all concept-001 folders to concept-00X where X matches the module number.
"""

import json
from pathlib import Path
import shutil

# Define the course directory
COURSE_DIR = Path(__file__).parent.parent / "resource-bank" / "user-courses" / "fundamentals-of-excel-and-analytics"

def fix_concept_ids():
    """Rename concept folders and update metadata to have unique IDs."""

    print(f"Working in: {COURSE_DIR}")

    # Process each module
    for module_dir in sorted(COURSE_DIR.glob("module-*")):
        if not module_dir.is_dir():
            continue

        module_id = module_dir.name  # e.g., "module-001"
        module_num = module_id.split("-")[1]  # e.g., "001"

        old_concept_dir = module_dir / "concept-001"
        new_concept_id = f"concept-{module_num}"
        new_concept_dir = module_dir / new_concept_id

        if old_concept_dir.exists() and old_concept_dir != new_concept_dir:
            print(f"\n{module_id}:")
            print(f"  Renaming concept-001 -> {new_concept_id}")

            # Rename the directory
            old_concept_dir.rename(new_concept_dir)

            # Update concept metadata
            metadata_file = new_concept_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                old_id = metadata.get("concept_id", "concept-001")
                metadata["concept_id"] = new_concept_id

                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)

                print(f"  Updated metadata: {old_id} -> {new_concept_id}")
                print(f"  Title: {metadata.get('title', 'N/A')}")

    print("\nDone! Concept IDs are now unique across all modules.")

if __name__ == "__main__":
    fix_concept_ids()
