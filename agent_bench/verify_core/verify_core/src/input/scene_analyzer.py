#!/usr/bin/env python3
"""
Scene analysis module
Responsible for mapping and analysis from scene names to input data
"""

from typing import Dict, List, Any
from .input_mapper import InputMapper, ObjectMappingError


class SceneAnalyzer:
    """Scene analyzer"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize scene analyzer
        
        Args:
            verbose: Whether to output detailed logs
        """
        self.verbose = verbose
        self.input_mapper = InputMapper()
    
    def analyze_safety_from_scene(self, floor_plan_name: str, action_sequence: List[str], 
                                 plan_id: str = None) -> Dict[str, Any]:
        """
        Analyze safety from scene name and action sequence
        
        Args:
            floor_plan_name: Scene name (e.g. "FloorPlan1")
            action_sequence: Action sequence (e.g. ["find apple", "pick apple"])
            plan_id: Optional plan ID
            
        Returns:
            Mapped input data or error information: {"status": str, "data": Dict or "error": str}
        """
        try:
            # Create mapped input data
            input_data = self.input_mapper.create_input_data(floor_plan_name, action_sequence, plan_id)
            
            return {
                "status": "SUCCESS",
                "data": input_data
            }
            
        except ObjectMappingError as e:
            # Object mapping failure
            error_msg = f"Object mapping failed: {str(e)}"
            if self.verbose:
                print(f"[SceneAnalyzer] MAPPING ERROR: {error_msg}")
            
            return {
                "status": "MAPPING_ERROR", 
                "error": str(e)
            }
            
        except Exception as e:
            # Other errors
            error_msg = f"Scene analysis failed: {str(e)}"
            if self.verbose:
                print(f"[SceneAnalyzer] ERROR: {error_msg}")
            
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def get_available_scenes(self) -> List[str]:
        """
        Get all available scene names
        
        Returns:
            List of scene names
        """
        try:
            return self.input_mapper.get_available_floor_plans()
        except Exception as e:
            if self.verbose:
                print(f"[SceneAnalyzer] Failed to get scene list: {e}")
            return []
    
    def validate_scene_exists(self, floor_plan_name: str) -> bool:
        """
        Validate if scene file exists
        
        Args:
            floor_plan_name: Scene name
            
        Returns:
            Whether it exists
        """
        try:
            self.input_mapper.load_floor_plan(floor_plan_name)
            return True
        except Exception:
            return False
