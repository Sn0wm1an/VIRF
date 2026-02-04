from dds_cloudapi_sdk import Config
from dds_cloudapi_sdk.tasks.v2_task import create_task_with_local_image_auto_resize
import os
import json
import base64
from dotenv import load_dotenv
from openai import OpenAI

api_path = "/v2/task/dinox/detection"


def detect_objects_DINOX(image_path: str, prompt_text: str) -> list:
    """
    Detect objects in an image using DINO-X API

    Args:
        image_path (str): Local path to the image file
        prompt_text (str): prompt text like "Apple.Pot.Egg"
    Returns:
        list: Detection results in the specified format [{box_id, box_coords, initial_label, score}]
    """
    token = os.getenv("DDS_TOKEN")
    assert token != None, "please set DDS_TOKEN"

    api_body = {
        "model": "DINO-X-1.0",
        "prompt": {"type": "text", "text": prompt_text},
        "targets": ["bbox"],
        #        "bbox_threshold": 0.15,
        #        "iou_threshold": 0.5
    }

    task = create_task_with_local_image_auto_resize(
        api_path=api_path,
        api_body_without_image=api_body,
        image_path=image_path,
    )

    task.set_request_timeout(10)
    task.run(Config(token))

    result = task.result

    #    print(result)

    res = []

    if result and "objects" in result:
        objects: list = result["objects"]
        for i, obj in enumerate(objects):
            formatted_result = {
                "box_id": f"obj_{i+1}",
                "box_coords": obj.get("bbox", []),
                "initial_label": obj.get("category", ""),
                "score": float(obj["score"]),
            }
            res.append(formatted_result)

    return res




def detect_objects_VLM(image_path: str, prompt_text: str) -> list:
    """
    Detect objects in an image using LLM

    Args:
        image_path (str): Local path to the image file
        prompt_text (str): prompt text like "Apple.Pot.Egg"
    Returns:
        list: Detection results in the specified format [{box_id, box_coords, initial_label, score}]
    """
    load_dotenv()
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL")
    
    if not api_key:
        raise ValueError("API_KEY environment variable not set.")
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # Convert image to base64
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Parse object categories from prompt_text
    object_categories = prompt_text.split('.')
    categories_str = ', '.join(object_categories)
    
    # Build LLM prompt
    prompt = f"""
Please analyze the objects in this image and identify objects of the following categories: {categories_str}

Please return the detection results in JSON format as follows:
{{
    "objects": [
        {{
            "bbox": [x1, y1, x2, y2],
            "category": "object_category_name",
            "score": 1.0
        }}
    ]
}}

Notes:
1. bbox coordinate format is [top_left_x, top_left_y, bottom_right_x, bottom_right_y]
2. Only detect the mentioned object categories
3. score is the object confidence score
4. If no objects are detected, return an empty objects array
5. Only return JSON format, do not include other text

Categories to detect: {categories_str}
"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
        )
        
        # Parse LLM response
        result = json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        # Return empty result
        result = {"objects": []}
    
    print("____________________________________________________________")
    print(result)

    res = []

    if result and "objects" in result:
        objects: list = result["objects"]
        for i, obj in enumerate(objects):
            formatted_result = {
                "box_id": f"obj_{i+1}",
                "box_coords": obj.get("bbox", []),
                "initial_label": obj.get("category", ""),
                "score": 1.0,  # Force confidence to 1.0
            }
            res.append(formatted_result)

    return res