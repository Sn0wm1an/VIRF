import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# --- Add all necessary source directories to the Python path ---
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.append(str(project_root / "src"))



# --- Module Imports from local copies ---
# Visual
from src.crop_and_encode_objects import crop_and_encode_objects
from src.tag_objects_with_llm import tag_objects_with_llm
from src.get_location_relationships import get_location_relationships_with_llm
from src.constants import LABELS
from src.ontology_parser import get_leaf_classes, get_leaf_properties



# --- Pipeline Functions ---


def run_visual_pipeline(image_dir: str, output_file: str, method: str = "DINOX"):
    """
    Runs the complete scene analysis pipeline: object detection, cropping and tagging, generating knowledge graph.
    """
    load_dotenv()

    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL")

    if not api_key:
        raise ValueError("API_KEY environment variable not set.")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # --- Extract labels from ontology files ---
    project_root = Path(__file__).parent
    material_owl_path = project_root / "ontology/core/material.owl"
    state_owl_path = project_root / "ontology/core/state.owl"
    relation_owl_path = project_root / "ontology/core/relation.owl"

    # Parse materials: automatically get all most specific material categories
    allowed_materials = get_leaf_classes(str(material_owl_path))

    # Parse states: automatically get all most specific state categories
    allowed_states = get_leaf_classes(str(state_owl_path))

    # Parse relations: automatically get all most specific relation properties
    allowed_relations = get_leaf_properties(str(relation_owl_path))

    print(f"  [Visual] Found {len(allowed_materials)} materials, {len(allowed_states)} states, and {len(allowed_relations)} relations.")

    print(allowed_materials),
    print(allowed_states)
    print(allowed_relations)


    print(f"  [Visual] Starting object processing pipeline using {method} method...")
    processed_objects = crop_and_encode_objects(
        image_dir=image_dir, prompt_text=".".join(LABELS), method=method
    )

    if not processed_objects:
        print("  [Visual] No objects were detected or processed.")
        return None

    # print("  [Visual] Processed objects: {}".format(processed_objects))

    tagged_objects = tag_objects_with_llm(
        client=client, model_name=model_name, processed_objects=processed_objects, allowed_materials=allowed_materials, allowed_states=allowed_states,
    )
    print("  [Visual] Tagged objects: {}".format(tagged_objects))
    locations = get_location_relationships_with_llm(
        client=client,
        model_name=model_name,
        image_dir=image_dir,
        processed_objects=processed_objects,
        allowed_relations=allowed_relations,
    )
    print("  [Visual] Locations: {}".format(locations))

    # --- Data Transformation ---
    instances = []
    assertions = []
    instance_counters = {}
    material_counters = {}
    state_counters = {}
    label_to_instance_name = {}

    # First pass: Create instances for all detected objects
    for obj in tagged_objects:
        class_name = obj["label"]
        if class_name not in instance_counters:
            instance_counters[class_name] = 0
        instance_counters[class_name] += 1
        instance_name = f"{class_name}_{instance_counters[class_name]}"
        
        instances.append({"class_name": class_name, "instance_name": instance_name})
        # Map unique ID to instance name for material/state assertions
        label_to_instance_name[obj["id"]] = instance_name
        
        # Map class name to the first instance name found, for relationship assertions
        if class_name not in label_to_instance_name:
            label_to_instance_name[class_name] = instance_name


    # Second pass: Create assertions for materials and states
    for obj in tagged_objects:
        subject_instance_name = label_to_instance_name[obj["id"]]

        # Material assertions
        material_name = obj.get("material")
        if material_name and material_name != "unknown":
            material_class_name = material_name
            if material_class_name not in material_counters:
                material_counters[material_class_name] = 0
            material_counters[material_class_name] += 1
            material_instance_name = f"{material_class_name}_{material_counters[material_class_name]}"



            instances.append({"class_name": material_class_name, "instance_name": material_instance_name})

            assertions.append({
                "subject": subject_instance_name,
                "property": "hasMaterial",
                "object": material_instance_name,
                "type": "material"
            })

        # State assertions
        for state in obj.get("state", []):
            # state 变量现在是状态的类名，例如 "CleanState"
            state_class_name = state

            # 使用计数器创建唯一的实例名
            if state_class_name not in state_counters:
                state_counters[state_class_name] = 0
            state_counters[state_class_name] += 1
            state_instance_name = f"{state_class_name}_{state_counters[state_class_name]}"

            instances.append({"class_name": state_class_name, "instance_name": state_instance_name})

            # 创建断言，并使用新的实例名作为 object
            assertions.append({
                "subject": subject_instance_name,
                "property": "hasState",
                "object": state_instance_name,
                "type": "state"
            })

    # Third pass: Create relationship assertions
    for loc in locations:
        subject_name = loc.get("first")
        object_name = loc.get("second")
        relationship = loc.get("relationship", "isNear").replace(" ", "")

        if subject_name in label_to_instance_name and object_name in label_to_instance_name:
            assertions.append({
                "subject": label_to_instance_name[subject_name],
                "property": relationship,
                "object": label_to_instance_name[object_name],
                "type": "relation"
            })


    final_output = {"instances": instances, "assertions": assertions}
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)

    print(f"  [Visual] Pipeline complete. Results saved to {output_file}")
    return final_output



# --- Main Orchestrator ---


def main():
    """
    Main orchestrator for the Scene Knowledge Graph Generator.
    """
    parser = argparse.ArgumentParser(description="Scene Knowledge Graph Generator")
    parser.add_argument(
        "--image_dir",
        type=str,
        default="visual_data",
        help="Directory containing the scene images.",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        help="Output file path.",
    )
    parser.add_argument(
        "--detection_method",
        type=str,
        choices=["DINOX", "VLM"],
        default="DINOX",
        help="Object detection method to use (DINOX or VLM). Default: DINOX",
    )
    args = parser.parse_args()

    print("Starting Scene Knowledge Graph Generator...")
    print(f"Image Directory: {args.image_dir}")
    print(f"Detection Method: {args.detection_method}")

    # --- Configuration ---
    output_dir = project_root / "output"
    os.makedirs(output_dir, exist_ok=True)

    # --- Input Data ---
    image_dir = project_root / args.image_dir

    image_paths = [
        str(p)
        for p in image_dir.glob("*")
        if p.suffix.lower() in [".png", ".jpg", ".jpeg"]
    ]
    if not image_paths:
        print(f"❌ Error: No images found in the directory '{image_dir}'.")
        return

    # --- Intermediate & Output File Paths ---
    environment_json_path = output_dir / "environment.json"

    if args.output_file:
        environment_json_path = Path(args.output_file)
    else:
        # If --output_file is not provided, use the default name
        environment_json_path = output_dir / "environment.json"

    run_visual_pipeline(str(image_dir), environment_json_path, args.detection_method)

if __name__ == "__main__":
    main()
