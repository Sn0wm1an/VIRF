"""
State world data model definitions
Contains data classes for action step results and action sequence results
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class ActionStepResult:
    """Individual action step result"""
    step_number: int
    action: str
    parameters: Dict[str, str]
    success: bool
    hazards: List[Dict[str, Any]]
    errors: List[str]
    world_state_after: Dict[str, Any]
    validation_result: Optional[Dict[str, Any]] = None  # World state validation result
    world_snapshot: Optional[Dict[str, Any]] = None     # World state snapshot


@dataclass
class ActionSequenceResult:
    """Action sequence processing result"""
    success: bool
    total_steps: int
    successful_steps: int
    failed_steps: int
    hazard_steps: int
    step_results: List[ActionStepResult]
    final_world_state: Dict[str, Any]
    errors: List[str]
