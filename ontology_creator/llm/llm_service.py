"""
Simplified LLM service module
Provides minimal viable LLM calling interface, supports system/user separation structure
"""

try:
    # Try relative import (when used as package)
    from .llm_client import call_llm_with_prompt
    from .prompts import format_prompt, get_prompt, list_prompts, add_prompt
except ImportError:
    # Fallback to absolute import (when run directly)
    from llm_client import call_llm_with_prompt
    from prompts import format_prompt, get_prompt, list_prompts, add_prompt

def call_llm(prompt_key: str, *args, **kwargs) -> str:
    """
    Call LLM using prompt key
    
    Args:
        prompt_key: Prompt key, e.g. "Step1_prompt"
        *args: Positional arguments, fill prompt template in order
        **kwargs: Keyword arguments, containing template parameters and LLM parameters
        
    Returns:
        str: LLM response result
        
    Examples:
        # Using positional arguments
        result = call_llm("Step1_prompt", "This is text to summarize")
        
        # Using keyword arguments
        result = call_llm("Step2_prompt", text="Hello", target_language="Chinese")
        
        # With LLM parameters
        result = call_llm("Step1_prompt", "text", temperature=0.3)
    """
    # Separate LLM parameters and template parameters
    llm_params = {}
    template_params = {}
    
    llm_param_keys = {'temperature', 'max_tokens'}
    for key, value in kwargs.items():
        if key in llm_param_keys:
            llm_params[key] = value
        else:
            template_params[key] = value
    
    # Format prompt - now returns (system_prompt, user_prompt) tuple
    system_prompt, user_prompt = format_prompt(prompt_key, *args, **template_params)
    
    # Call LLM
    return call_llm_with_prompt(user_prompt, system_prompt=system_prompt, **llm_params)

def call_llm_direct(prompt: str, system_prompt: str = "", **kwargs) -> str:
    """
    Call LLM directly with prompt
    
    Args:
        prompt: Direct prompt text
        system_prompt: System prompt
        **kwargs: LLM parameters
        
    Returns:
        str: LLM response result
    """
    return call_llm_with_prompt(prompt, system_prompt=system_prompt, **kwargs)

def get_available_prompts():
    """Get all available prompt keys"""
    return list_prompts()

def add_custom_prompt(key: str, system_prompt: str, user_template: str):
    """Add custom prompt"""
    add_prompt(key, system_prompt, user_template)
