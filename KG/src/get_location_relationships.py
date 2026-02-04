import json
import os
import base64
from openai import OpenAI
from typing import List, Dict, Any


def _encode_image(image_path: str) -> str:
    """Helper function to encode an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_location_relationships_with_llm(
    client: OpenAI,
    model_name: str,
    image_dir: str,
    processed_objects: List[Dict[str, Any]],
    allowed_relations: List[str] = None
) -> List[Dict[str, str]]:
    """
    Analyzes the spatial relationships between objects using an LLM by observing the original images.

    Args:
        client (OpenAI): An initialized OpenAI client instance.
        model_name (str): The name of the model to use.
        image_dir (str): The directory containing the original images.
        processed_objects (list): A list of dictionaries, each representing a detected object.

    Returns:
        list: A list of dictionaries describing the relationships between objects.
              Example: [{"first": "Apple", "relationship": "on", "second": "CounterTop"}]
    """
    if not processed_objects:
        return []

    # 如果未提供允许的关系列表，则初始化为空列表
    if allowed_relations is None:
        allowed_relations = []

    object_labels = [obj["initial_label"] for obj in processed_objects]
    image_paths = [
        os.path.join(image_dir, f)
        for f in os.listdir(image_dir)
        if f.endswith((".png", ".jpg", ".jpeg"))
    ]

    if not image_paths:
        return []

    relation_prompt = (
        f"The 'relationship' must be chosen from the following list: {json.dumps(allowed_relations, ensure_ascii=False)}."
        if allowed_relations
        else "Determine the most appropriate spatial relationship."
    )

    # Construct the prompt with all original images and the list of detected labels
    prompt_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """
Analyze the following scene images. Based on the spatial arrangement of the objects, describe the relationships between them.
The detected object labels in the scene are: {labels}.

Your task is to identify the relationships between pairs of these objects.
Return a JSON object containing a list called "locations". Each item in the list must be a dictionary with three keys: "first", "relationship", and "second".
{relation_instruction}
- "first": The label of the first object from the provided list.
- "relationship": The spatial relationship.
- "second": The label of the second object from the provided list.

Example output format:
{{
  "locations": [
    {{
      "first": "Apple",
      "relationship": "isOn",
      "second": "CounterTop"
    }},
    {{
      "first": "Cup",
      "relationship": "isNextTo",
      "second": "Book"
    }}
  ]
}}

Return only the JSON object, without any additional text or markdown formatting.
""".format(
                        labels=", ".join(object_labels),
                        relation_instruction=relation_prompt
                    ),
                }
            ],
        }
    ]

    # Add original image URLs to the prompt
    for image_path in image_paths:
        base64_image = _encode_image(image_path)
        prompt_messages[0]["content"].append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            }
        )

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=prompt_messages,  # type: ignore
            response_format={"type": "json_object"},
        )
        # print(response.choices[0].message.content)
        llm_response_data = json.loads(str(response.choices[0].message.content))
        return llm_response_data.get("locations", [])

    except Exception as e:
        print(f"Error getting location relationships: {e}")
        return []
