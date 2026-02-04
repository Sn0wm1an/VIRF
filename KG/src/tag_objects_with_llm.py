import os
import json
import concurrent.futures
from openai import OpenAI
from typing import Optional, List


def _get_tags_for_image(
        client: OpenAI,
        model_name: str,
        cropped_object: dict,
        allowed_materials: List[str],
        allowed_states: List[str]
) -> Optional[dict]:
    """
    Helper function to get tags for a single cropped image using OpenAI's API.
    """
    image_b64 = cropped_object["image"].split(",")[1]
    initial_label = cropped_object["initial_label"]

    # --- Create prompts using allowed values ---
    material_prompt = f"Please choose one from the following list: {json.dumps(allowed_materials, ensure_ascii=False)}" if allowed_materials else ""
    state_prompt = f"Please choose any relevant states from the following list: {json.dumps(allowed_states, ensure_ascii=False)}" if allowed_states else ""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
Analyze the following image of a '{initial_label}'.
Based on the image, describe its properties in a JSON format.

The JSON object must include the following keys:
- "state": An array of strings describing the current state of the object. {state_prompt}
- "material": A string describing the primary material of the object. {material_prompt}

Here is an example of the expected JSON output for an image of a kitchen knife:
{{
  "state": [],
  "material": "metal"
}}

"material" can be "unknown"

Return only the JSON object, without any additional text or markdown formatting.
""",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
        )
        # print("!!!!!!!!!!!!!!\n")
        # print(response.choices[0].message.content)
        # print("!!!!!!!!!!!!!!\n")
        llm_response_data = json.loads(str(response.choices[0].message.content))
        # Combine original data with LLM response
        final_object = {
            "id": f"{initial_label.lower().replace(' ', '_')}_{os.urandom(2).hex()}",
            "label": initial_label,
            "confidence": cropped_object.get(
                "score", 0.9
            ),  # Use score if available, otherwise default
            "state": llm_response_data.get("state", []),
            "material": llm_response_data.get("material", "unknown"),
            "tags": llm_response_data.get("tags", []),
        }
        return final_object

    except Exception as e:
        print(f"Error processing object '{initial_label}': {e}")
        return None


def tag_objects_with_llm(
    client: OpenAI, model_name: str, processed_objects: list, allowed_materials: List[str] = None, allowed_states: List[str] = None
) -> list:
    """
    Tags a list of cropped objects using an LLM in parallel.

    Args:
        client (OpenAI): An initialized OpenAI client instance.
        model_name (str): The name of the model to use for tagging.
        processed_objects (list): A list of dictionaries from crop_and_encode_objects.

    Returns:
        list: A list of dictionaries with detailed tags from the LLM.
    """

    if allowed_materials is None:
        allowed_materials = []
    if allowed_states is None:
        allowed_states = []

    tagged_objects = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_object = {
            executor.submit(_get_tags_for_image, client, model_name, obj, allowed_materials, allowed_states): obj
            for obj in processed_objects
        }
        for future in concurrent.futures.as_completed(future_to_object):
            try:
                result = future.result()
                if result:
                    tagged_objects.append(result)
            except Exception as exc:
                obj = future_to_object[future]
                print(
                    f"Object '{obj['initial_label']}' generated an exception during tagging: {exc}"
                )

    return tagged_objects
