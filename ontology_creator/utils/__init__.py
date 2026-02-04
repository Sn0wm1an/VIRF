"""
LLM calling and prompt management module
Provides minimal viable LLM calling functionality
"""

from llm.llm_client import call_llm
from llm.prompts import get_prompt, format_prompt, add_prompt, list_prompts

__version__ = "1.0.0"
__author__ = "ICLR Ontology Creator"

# Export main interfaces
__all__ = [
    # Core functions
    "call_llm",           # Main calling interface
    
    # Prompt management
    "get_prompt",
    "format_prompt", 
    "add_prompt",
    "add_custom_prompt",
    "list_prompts",
    "get_available_prompts",
    
    # Lower-level interfaces
    "LLMClient",
    "call_llm_with_prompt"
]
