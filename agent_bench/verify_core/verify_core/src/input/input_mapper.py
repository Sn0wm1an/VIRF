#!/usr/bin/env python3
"""
Input mapping module
Responsible for mapping scene names and action sequences to standardized input format
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ObjectMappingError(Exception):
    """Exception thrown when objects in action sequence cannot find corresponding instances in scene"""
    pass


class InputMapper:
    """Input mapper"""
    
    def __init__(self, environment_dir: str = None):
        """
        Initialize input mapper
        
        Args:
            environment_dir: Environment data directory path
        """
        if environment_dir is None:
            # Use relative path by default - find data/Environment from src/input directory
            current_dir = os.path.dirname(os.path.abspath(__file__))  # verify_core/src/input/
            parent_dir = os.path.dirname(current_dir)  # verify_core/src/
            grandparent_dir = os.path.dirname(parent_dir)  # verify_core/
            self.environment_dir = os.path.join(grandparent_dir, 'data', 'Environment')
        else:
            self.environment_dir = environment_dir
            
        if not os.path.exists(self.environment_dir):
            raise ValueError(f"Environment directory not found: {self.environment_dir}")
    
    def load_floor_plan(self, floor_plan_name: str) -> Dict[str, Any]:
        """
        Load specified scene file
        
        Args:
            floor_plan_name: Scene name (e.g. "FloorPlan1", "FloorPlan30")
            
        Returns:
            Scene data dictionary
        """
        # Build file path
        file_path = os.path.join(self.environment_dir, f"{floor_plan_name}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Floor plan file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            return scene_data
        except Exception as e:
            raise RuntimeError(f"Failed to load floor plan {floor_plan_name}: {str(e)}")
    
    def _map_action_objects_to_instances(self, action_sequence: List[str], instances: List[dict]) -> List[str]:
        """
        Map object names in action sequence to actual instance names

        Args:
            action_sequence: Original action sequence (e.g. ["find apple", "pick apple"])
            instances: Instance list in scene

        Returns:
            Mapped action sequence (e.g. ["find Apple_1", "pick Apple_1"])
        """
        # Create class name to instance name mapping dictionary (case insensitive)
        class_to_instance = {}
        for instance in instances:
            class_name = instance["class_name"].lower()
            instance_name = instance["instance_name"]
            if class_name not in class_to_instance:
                class_to_instance[class_name] = instance_name

        # Define multi-word verbs
        multi_word_verbs = ["turn on", "turn off", "fill liquid", "empty liquid", "put in"]

        mapped_actions = []
        missing_objects = []
        
        for action in action_sequence:
            parts = action.split()
            mapped_action = action  # Keep original by default
            
            # Check if it's a multi-word verb
            if any(action.lower().startswith(verb.lower() + " ") for verb in multi_word_verbs):
                for verb in multi_word_verbs:
                    if action.lower().startswith(verb.lower() + " "):
                        # Extract object name (remove verb part)
                        obj_name = action[len(verb):].strip().lower()
                        
                        # Find corresponding instance name
                        if obj_name in class_to_instance:
                            mapped_action = f"{verb} {class_to_instance[obj_name]}"
                        else:
                            logger.warning(f"No instance found for object: {obj_name} in action: {action}")
                            missing_objects.append(obj_name)
                        break
            
            # Handle "put" action (not including "in")
            elif action.lower().startswith("put ") and len(parts) >= 2:
                obj_name = parts[1].lower()
                if obj_name in class_to_instance:
                    mapped_action = f"put {class_to_instance[obj_name]}"
                else:
                    logger.warning(f"No instance found for object: {obj_name} in action: {action}")
                    missing_objects.append(obj_name)
            
            # Handle single-word verbs
            elif len(parts) >= 2:
                obj_name = parts[1].lower()
                if obj_name in class_to_instance:
                    mapped_action = f"{parts[0]} {class_to_instance[obj_name]}"
                else:
                    logger.warning(f"No instance found for object: {obj_name} in action: {action}")
                    missing_objects.append(obj_name)
            # Single-word actions (like "drop"), keep original - mapped_action is already action
            
            mapped_actions.append(mapped_action)
        
        # If there are missing objects, throw exception
        if missing_objects:
            raise ObjectMappingError(f"Cannot find corresponding instances for the following objects in scene: {', '.join(missing_objects)}")

        return mapped_actions
    
    def create_input_data(self, floor_plan_name: str, action_sequence: List[str], plan_id: str = None) -> Dict[str, Any]:
        """
        Create standardized input data
        
        Args:
            floor_plan_name: Scene name
            action_sequence: Action sequence
            plan_id: Plan ID
            
        Returns:
            Standardized input data
        """
        # Load scene data
        scene_data = self.load_floor_plan(floor_plan_name)
        
        # Map action sequence to instances
        instances = scene_data.get("instances", [])
        mapped_actions = self._map_action_objects_to_instances(action_sequence, instances)
        
        # Create standardized input format
        input_data = {
            "instances": instances,
            "assertions": scene_data.get("assertions", []),
            "action_sequence": mapped_actions
        }
        
        # Add optional plan ID
        if plan_id:
            input_data["plan_id"] = plan_id
        
        return input_data
    
    def get_available_floor_plans(self) -> List[str]:
        """
        Get all available scene names
        
        Returns:
            List of scene names
        """
        floor_plans = []
        
        if not os.path.exists(self.environment_dir):
            return floor_plans
            
        for filename in os.listdir(self.environment_dir):
            if filename.endswith('.json'):
                # Remove .json suffix
                floor_plan_name = filename[:-5]
                floor_plans.append(floor_plan_name)
                
        return sorted(floor_plans)


def create_mapped_input(floor_plan_name: str, action_sequence: List[str], 
                       environment_dir: str = None, plan_id: str = None) -> Dict[str, Any]:
    """
    Convenience function: Create mapped input data
    
    Args:
        floor_plan_name: Scene name
        action_sequence: Action sequence
        environment_dir: Environment data directory path
        plan_id: Plan ID
        
    Returns:
        Mapped input data
    """
    mapper = InputMapper(environment_dir)
    return mapper.create_input_data(floor_plan_name, action_sequence, plan_id)
