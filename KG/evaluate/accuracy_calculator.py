import os
import json
from ai2thor.controller import Controller

project_root = os.path.dirname(os.path.abspath(__file__))

def calculate(scene_number: int, controller: Controller) -> None:
    print(f"==============Scence{scene_number}==============")
    environment_data_path = os.path.join(project_root, 'output_1', f'environment{scene_number}.json')
    try:
        with open(environment_data_path, 'r', encoding='utf-8') as json_file:
            environment_data = json.load(json_file)
    except FileNotFoundError as e:
        print(f"Error, environment data not found for scene{scene_number}")
        return
    except json.JSONDecodeError as e:
        print(f"Error, json format is not correct for scene{scene_number}")

    if "instances" in environment_data:
        instance_data = environment_data.get("instances")
        print("Total generated instances number:", len(instance_data))
        classes_data = {instance["class_name"] for instance in instance_data if instance["class_name"]}
        print("Total generated classes number:", len(classes_data))
    else:
        print("Instances not found")
        return

    controller.reset(scene=f"FloorPlan{scene_number}")
    objects_data = {obj["objectType"] for obj in controller.last_event.metadata["objects"]}
    print("Total official objects number:", len(objects_data))
    same_count = 0
    for class_name in classes_data:
        if class_name in objects_data:
            same_count += 1
    accuracy = (same_count / len(objects_data)) * 100
    print("Accuracy:", accuracy)

if __name__ == "__main__":
    controller = Controller()
    for scene_number in range(1, 31):
        calculate(scene_number, controller)
    controller.stop()


