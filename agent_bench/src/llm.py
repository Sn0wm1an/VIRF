import os
from openai import OpenAI
from .logger import logger

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
client = OpenAI(api_key=api_key, base_url=base_url)
default_model = os.getenv("MODEL")

# Global counter for LLM calls, used to print full prompts for first N calls
_llm_call_counter = 0
_max_full_prompt_prints = 10


def ask_llm(
    prompt: str, image: str | None = None, extra_messages: list[dict] | None = None
):
    global _llm_call_counter
    _llm_call_counter += 1
    
    # Print full prompt for first N calls (for testing and verification)
    if _llm_call_counter <= _max_full_prompt_prints:
        print("\n" + "="*100)
        print(f"🔍 LLM CALL #{_llm_call_counter} - FULL PROMPT (Testing Mode)")
        print("="*100)
        print(prompt)
        print("="*100)
        print(f"Prompt length: {len(prompt)} characters")
        print("="*100 + "\n")
        logger.info("LLM Call #%d - Full prompt printed to stdout (length: %d chars)", 
                   _llm_call_counter, len(prompt))
    else:
        logger.info("LLM Call #%d - %s", _llm_call_counter, prompt.strip().splitlines()[0] + "...")

    if image and os.environ.get("HACK_QWEN_NO_IMAGE") != "1":
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}},
                ],
            }
        ]
    else:
        messages = [{"role": "user", "content": prompt}]

    if extra_messages:
        messages.extend(extra_messages)

    response = client.chat.completions.create(
        model=default_model,  # type: ignore
        messages=messages,  # type: ignore
        temperature=0.1,
        timeout=120,  
    )
    content = response.choices[0].message.content
    assert isinstance(content, str)
    logger.info("LLM Response: %s", content)
    return content
