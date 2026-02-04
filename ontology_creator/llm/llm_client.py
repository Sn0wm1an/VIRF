import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, Dict, Any

class LLMClient:
    """LLM client for calling configured large language models"""
    
    def __init__(self):
        """Initialize LLM client, load configuration from .env file"""
        # Load environment variables
        load_dotenv()
        
        # Get configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model_id = os.getenv("OPENAI_MODEL_ID")
        
        if not all([self.api_key, self.base_url, self.model_id]):
            raise ValueError("Missing required environment variable configuration, please check OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL_ID in .env file")
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def extract_json_from_markdown(self, text: str) -> str:
        """
        Extract JSON content from markdown code blocks
        
        Args:
            text: Text containing markdown code blocks
            
        Returns:
            str: Extracted JSON string, returns original text if not found
        """
        # Match content between ```json and ```
        json_pattern = r'```json\s*\n([\s\S]*?)\n```'
        match = re.search(json_pattern, text)
        
        if match:
            return match.group(1).strip()
        
        # If no json code block found, try to match general ``` code blocks
        general_pattern = r'```\s*\n([\s\S]*?)\n```'
        match = re.search(general_pattern, text)
        
        if match:
            content = match.group(1).strip()
            # Simple check if it might be JSON (starts with { and ends with })
            if content.startswith('{') and content.endswith('}'):
                return content
        
        # If nothing found, return original text
        return text
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """
        Call LLM and return result
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Temperature parameter, controls output randomness
            max_tokens: Maximum output tokens (optional)
            
        Returns:
            str: LLM response result (automatically extracts content from markdown code blocks if present)
        """
        try:
            messages = []
            
            # Add system prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add user prompt
            messages.append({"role": "user", "content": prompt})
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            
            # Try to extract JSON content from markdown code blocks
            extracted_result = self.extract_json_from_markdown(result)
            
            return extracted_result
            
        except Exception as e:
            raise Exception(f"Error occurred when calling LLM: {str(e)}")
    
    def get_model_info(self) -> Dict[str, str]:
        """Get current model configuration information"""
        return {
            "model_id": self.model_id,
            "base_url": self.base_url,
            "api_key_prefix": self.api_key[:10] + "..." if self.api_key else None
        }


# Global LLM client instance
llm_client = LLMClient()

def call_llm_with_prompt(prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
    """
    Convenience function: Call LLM with prompt
    
    Args:
        prompt: User prompt
        system_prompt: System prompt (optional)
        **kwargs: Other parameters (temperature, max_tokens, etc.)
        
    Returns:
        str: LLM response result
    """
    return llm_client.call_llm(prompt, system_prompt, **kwargs)

def call_llm(prompt_key: str, **kwargs) -> str:
    """
    Convenience function: Call LLM based on prompt key
    
    Args:
        prompt_key: Prompt key name (e.g. "entity_extraction", "structured_rule_generation")
        **kwargs: Other parameters, such as text, system_prompt, temperature, etc.
        
    Returns:
        str: LLM response result
    """
    # Extract text from kwargs as main prompt content
    text = kwargs.get('text', '')
    system_prompt = kwargs.get('system_prompt', None)
    
    # Remove these parameters to avoid errors when passing to OpenAI API
    filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['text', 'system_prompt']}
    
    return llm_client.call_llm(text, system_prompt, **filtered_kwargs)
