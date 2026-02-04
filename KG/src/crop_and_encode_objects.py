import os
import base64
import concurrent.futures
from io import BytesIO
from PIL import Image

from detect_objects import detect_objects_DINOX

from detect_objects import detect_objects_VLM


def _detect_objects_in_image(image_path: str, prompt_text: str, method: str = "DINOX") -> list:
    """Helper function to detect objects in a single image."""
    if method == "VLM":
        detected_objects = detect_objects_VLM(image_path=image_path, prompt_text=prompt_text)
    else:  
        detected_objects = detect_objects_DINOX(image_path=image_path, prompt_text=prompt_text)
    
    for obj in detected_objects:
        obj["image_path"] = image_path
    return detected_objects


def _crop_and_encode_image(label: str, obj_data: dict) -> dict:
    """Helper function to crop and encode a single object image."""
    image_path = obj_data["image_path"]
    box_coords = obj_data["box_coords"]
    score = obj_data["score"]

    with Image.open(image_path) as img:
        width, height = img.size
        left, top, right, bottom = box_coords

        # Add a 20% margin around the bounding box
        x_margin = (right - left) * 0.5
        y_margin = (bottom - top) * 0.5

        new_left = max(0, left - x_margin)
        new_top = max(0, top - y_margin)
        new_right = min(width, right + x_margin)
        new_bottom = min(height, bottom + y_margin)

        expanded_box_coords = (new_left, new_top, new_right, new_bottom)
        cropped_img = img.crop(expanded_box_coords)

        # Convert cropped image to base64 data URI
        buffered = BytesIO()
        cropped_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        mime_image_str = f"data:image/png;base64,{img_str}"

        return {"initial_label": label, "image": mime_image_str, "score": score}


def crop_and_encode_objects(image_dir: str, prompt_text: str, method: str = "DINOX") -> list:
    """
    Traverse all images in a directory, detect objects, deduplicate, crop, and encode them using multiple threads.

    Args:
        image_dir (str): The path to the directory containing images.
        prompt_text (str): A dot-separated string of object names to detect.
        method (str): Detection method to use ("DINOX" or "VLM"). Defaults to "DINOX".

    Returns:
        list: A list of dictionaries, where each dictionary contains the initial_label
              and the base64 encoded cropped image.
              e.g., [{'initial_label': 'Apple', 'image': 'data:image/png;base64,...'}, ...]
    """
    image_files = [
        os.path.join(image_dir, f)
        for f in os.listdir(image_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    # Parallel object detection
    all_detected_objects = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_image = {
            executor.submit(
                _detect_objects_in_image, image_path, prompt_text, method
            ): image_path
            for image_path in image_files
        }
        for future in concurrent.futures.as_completed(future_to_image):
            try:
                detected_objects = future.result()
                all_detected_objects.extend(detected_objects)
            except Exception as exc:
                image_path = future_to_image[future]
                print(f"{image_path} generated an exception: {exc}")

    # Deduplicate objects
    unique_objects = {}
    for obj in all_detected_objects:
        label = obj["initial_label"]
        box_coords = obj["box_coords"]
        score = obj["score"]

        if (not box_coords) or score < 0.5:
            continue

        if label not in unique_objects or score > unique_objects[label]["score"]:
            unique_objects[label] = {
                "box_coords": box_coords,
                "image_path": obj["image_path"],
                "score": score,
            }

    # Parallel image cropping and encoding
    result_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_label = {
            executor.submit(_crop_and_encode_image, label, obj_data): label
            for label, obj_data in unique_objects.items()
        }
        for future in concurrent.futures.as_completed(future_to_label):
            try:
                result = future.result()
                result_list.append(result)
            except Exception as exc:
                label = future_to_label[future]
                print(f"Object '{label}' generated an exception during cropping: {exc}")

    return result_list
