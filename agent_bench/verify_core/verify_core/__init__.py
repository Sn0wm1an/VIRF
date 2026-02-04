"""
Kitchen Environment Safety Analysis Package
Kitchen environment safety analysis package

Provides standardized API interface for action sequence safety detection
"""

from .safety_analyzer import SafetyAnalyzer, analyze_action_sequence_safety_from_file

__version__ = "1.0.0"
__author__ = "Kitchen Safety Team"
__email__ = "safety@kitchen.ai"

# Export main APIs
__all__ = [
    'SafetyAnalyzer',
    'analyze_safety',
    'analyze_action_sequence_safety_from_file',
]

# Convenient module-level function
def analyze_safety(input_data, verbose=False, max_workers=None):
    """
    Convenience function: Analyze the safety of action sequences
    
    Args:
        input_data (dict): Input data containing instances, assertions, and action sequences
        verbose (bool): Whether to output detailed logs
        max_workers (int): Maximum number of threads
        
    Returns:
        dict: Safety analysis results
    """
    analyzer = SafetyAnalyzer(verbose=verbose, max_workers=max_workers)
    return analyzer.analyze_safety(input_data)
