#!/usr/bin/env python3
"""
Safety checking core module
Handles safety verification logic for action sequences
"""

import tempfile
import json
import os
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from ...action_sequence_processor import MainActionSequenceProcessor


class SafetyChecker:
    """Safety checker"""
    
    def __init__(self, verbose: bool = False, max_workers: int = None):
        """
        Initialize safety checker
        
        Args:
            verbose: Whether to output detailed logs
            max_workers: Maximum number of threads, None means no limit
        """
        self.verbose = verbose
        self.max_workers = max_workers
        self.processor = None
    
    def run_safety_check_robust(self, input_file: str) -> Tuple[Dict[str, Any], List[str]]:
        """Run robust safety check"""
        results = None
        error_messages = []
        
        try:
            # Create new processor instance each time to avoid state pollution
            self.processor = MainActionSequenceProcessor(
                verbose=self.verbose
            )
            
            # Initialize world
            if not self.processor.initialize_world():
                error_messages.append("World initialization failed")
                return None, error_messages
            
            # Load scene
            scenario = self.processor.load_scenario_from_json(input_file)
            
            # Set initial world state
            if not self.processor.setup_initial_world_state(scenario):
                error_messages.append("Initial world state setup failed")
                return None, error_messages
            
            # Generate world state sequence
            state_sequence = self.processor.generate_world_state_sequence(
                scenario.get('action_sequence', []), 
                enable_reasoning=True,
                max_workers=self.max_workers
            )
            
            # Generate safety report
            results = self.processor.generate_safety_report(
                state_sequence, 
                scenario.get('plan_id', 'safety_check')
            )
            
            if self.verbose:
                print(f"[SafetyChecker] Processing completed, got result: {type(results)}")
                
        except Exception as e:
            # Catch all exceptions, log errors but don't interrupt
            error_message = f"Safety check execution failed: {str(e)}"
            error_messages.append(error_message)
            if self.verbose:
                print(f"[SafetyChecker] ERROR: {error_message}")
            
            # Return empty result, let upper layer handle
            results = None
        
        return results, error_messages
    
    def run_safety_check_from_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run safety check directly from input data"""
        error_messages = []
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
                json.dump(input_data, temp_file, indent=2, ensure_ascii=False)
                temp_file_path = temp_file.name
            
            if self.verbose:
                print(f"[SafetyChecker] Created temporary file: {temp_file_path}")
            
            try:
                # Run safety check
                results, check_errors = self.run_safety_check_robust(temp_file_path)
                error_messages.extend(check_errors)
                
                return results, error_messages
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                    if self.verbose:
                        print(f"[SafetyChecker] Temporary file cleaned up: {temp_file_path}")
                except:
                    pass  # Cleanup failure doesn't affect main process
                    
        except Exception as e:
            error_message = f"Failed to create temporary file: {str(e)}"
            error_messages.append(error_message)
            if self.verbose:
                print(f"[SafetyChecker] ERROR: {error_message}")
            
            return None, error_messages
    
    def check_input_data_validity(self, input_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Check validity of input data
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            (is_valid, error_messages): Whether valid and list of error messages
        """
        errors = []
        
        # Check required fields
        required_fields = ["instances", "action_sequence"]
        for field in required_fields:
            if field not in input_data:
                errors.append(f"Missing required field: {field}")
        
        # Check if instance list is empty
        if "instances" in input_data:
            instances = input_data["instances"]
            if not isinstance(instances, list):
                errors.append("instances must be a list")
            else:
                for i, instance in enumerate(instances):
                    if not isinstance(instance, dict):
                        errors.append(f"Instance {i} must be a dictionary")
                        continue
                    if "class_name" not in instance:
                        errors.append(f"Instance {i} missing class_name")
                    if "instance_name" not in instance:
                        errors.append(f"Instance {i} missing instance_name")
        
        # Check if action sequence is empty
        if "action_sequence" in input_data:
            actions = input_data["action_sequence"]
            if not isinstance(actions, list):
                errors.append("action_sequence must be a list")
            else:
                for i, action in enumerate(actions):
                    if not isinstance(action, str):
                        errors.append(f"Action {i} must be a string")
        
        return len(errors) == 0, errors
