"""
Expand each module to have multiple concepts - one per Module Learning Outcome (MLO).
"""

import json
from pathlib import Path
import shutil

# Define the course directory
COURSE_DIR = Path(__file__).parent.parent / "resource-bank" / "user-courses" / "fundamentals-of-excel-and-analytics"

def expand_concepts_from_mlos():
    """Create multiple concepts within each module based on MLOs."""

    print(f"Working in: {COURSE_DIR}")

    concept_counter = 1  # Global concept counter for unique IDs

    # Process each module
    for module_dir in sorted(COURSE_DIR.glob("module-*")):
        if not module_dir.is_dir():
            continue

        module_id = module_dir.name

        # Load module metadata
        module_metadata_path = module_dir / "metadata.json"
        if not module_metadata_path.exists():
            print(f"Skipping {module_id} - no metadata found")
            continue

        with open(module_metadata_path, "r", encoding="utf-8") as f:
            module_metadata = json.load(f)

        module_title = module_metadata.get("title", module_id)
        mlos = module_metadata.get("module_learning_outcomes", [])

        print(f"\n{module_id}: {module_title}")
        print(f"  MLOs: {len(mlos)}")

        # Remove existing concepts
        for old_concept in module_dir.glob("concept-*"):
            if old_concept.is_dir():
                print(f"  Removing old concept: {old_concept.name}")
                shutil.rmtree(old_concept)

        # Create new concepts - one per MLO
        concept_ids = []
        for mlo_index, mlo in enumerate(mlos):
            concept_id = f"concept-{str(concept_counter).zfill(3)}"
            concept_ids.append(concept_id)

            concept_dir = module_dir / concept_id
            concept_dir.mkdir(parents=True, exist_ok=True)

            # Create concept subdirectories
            (concept_dir / "resources").mkdir(exist_ok=True)
            (concept_dir / "assessments").mkdir(exist_ok=True)

            # Create concept metadata
            concept_metadata = {
                "concept_id": concept_id,
                "title": mlo,  # Use the MLO as the concept title
                "learning_objectives": [mlo],  # Single LO matching the MLO
                "prerequisites": []
            }

            with open(concept_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(concept_metadata, f, indent=2, ensure_ascii=False)

            print(f"  Created {concept_id}: {mlo[:60]}...")

            concept_counter += 1

        # Update module metadata with new concept list
        module_metadata["concepts"] = concept_ids
        with open(module_metadata_path, "w", encoding="utf-8") as f:
            json.dump(module_metadata, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Created {concept_counter - 1} concepts across all modules.")

if __name__ == "__main__":
    expand_concepts_from_mlos()
