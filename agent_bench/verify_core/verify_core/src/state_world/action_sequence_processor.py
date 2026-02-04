"""
State World Action Sequence Processor Main Coordinator: Coordinates the processing of action sequences
"""

from typing import List
import owlready2 as owl

from .data_models import ActionStepResult, ActionSequenceResult
from .world_state_manager import WorldStateManager
from .action_executor import ActionExecutor
from .action_semantics import parse_action_sequence


class ActionSequenceProcessor:
    """ State World Action Sequence Processor Main Coordinator"""
    
    def __init__(self, world: owl.World):
        """
        Initialize the processor
        
        Args:
            world: OWL world instance
        """
        self.world = world
        self.current_held_object = None
        self.last_found_object = None
        self.world_state_manager = WorldStateManager(world)
        self.action_executor = ActionExecutor(world)
    
    def process_action_sequence(self, action_sequence: List[str]) -> ActionSequenceResult:
        """
        Process an action sequence
        
        Args:
            action_sequence: List of action strings
            
        Returns:
            ActionSequenceResult: Action sequence processing result
        """
        print(f"🎬 Starting action sequence processing ({len(action_sequence)} actions)")
        
        step_results = []
        
        try:
            for step_num, action_str in enumerate(action_sequence, 1):
                print(f"\n--- Step {step_num}: {action_str} ---")
                
                # Parse action
                parsed_actions = parse_action_sequence([action_str])
                if not parsed_actions:
                    step_result = ActionStepResult(
                        step_number=step_num,
                        action=action_str,
                        parameters={},
                        success=False,
                        hazards=[],
                        errors=['Unable to parse action'],
                        world_state_after=self.world_state_manager.capture_world_state()
                    )
                    step_results.append(step_result)
                    continue
                
                action_name, parameters = parsed_actions[0]
                
                if 'current_held_object' in parameters.values() or 'last_found_object' in parameters.values():
                    for key, value in parameters.items():
                        if value == 'current_held_object':
                            if self.current_held_object:
                                parameters[key] = self.current_held_object
                            else:
                                step_result = ActionStepResult(
                                    step_number=step_num,
                                    action=action_str,
                                    parameters=parameters,
                                    success=False,
                                    hazards=[],
                                    errors=['No object being held'],
                                    world_state_after=self.world_state_manager.capture_world_state()
                                )
                                step_results.append(step_result)
                                continue
                        elif value == 'last_found_object':
                            if self.last_found_object:
                                parameters[key] = self.last_found_object
                            else:
                                step_result = ActionStepResult(
                                    step_number=step_num,
                                    action=action_str,
                                    parameters=parameters,
                                    success=False,
                                    hazards=[],
                                    errors=['No object found'],
                                    world_state_after=self.world_state_manager.capture_world_state()
                                )
                                step_results.append(step_result)
                                continue
                

                step_result = self._execute_single_action(step_num, action_name, parameters, action_str)
                step_results.append(step_result)
                

                if action_name == 'pick' and step_result.success:
                    self.current_held_object = parameters.get('object')
                elif action_name == 'put' and step_result.success:
                    self.current_held_object = None
                elif action_name == 'find' and step_result.success:
                    self.last_found_object = parameters.get('object')
                
                # If hazards are detected, output warning
                if step_result.hazards:
                    print(f"🚨 Detected {len(step_result.hazards)} hazard situations!")
                    for hazard in step_result.hazards:
                        print(f"   ⚠️ {hazard.get('feedback_message', 'Unknown hazard')}")
            
            # Calculate results
            successful_steps = sum(1 for r in step_results if r.success)
            failed_steps = sum(1 for r in step_results if not r.success)
            hazard_steps = sum(1 for r in step_results if r.hazards)
            
            return ActionSequenceResult(
                success=True,
                total_steps=len(step_results),
                successful_steps=successful_steps,
                failed_steps=failed_steps,
                hazard_steps=hazard_steps,
                step_results=step_results,
                final_world_state=self.world_state_manager.capture_world_state(),
                errors=[]
            )
            
        except Exception as e:
            print(f"❌ Action sequence processing failed: {e}")
            import traceback
            traceback.print_exc()
            
            return ActionSequenceResult(
                success=False,
                total_steps=len(step_results),
                successful_steps=0,
                failed_steps=len(step_results),
                hazard_steps=0,
                step_results=step_results,
                final_world_state=self.world_state_manager.capture_world_state(),
                errors=[str(e)]
            )
    
    def _execute_single_action(self, step_num: int, action_name: str, 
                              parameters: dict, original_action: str) -> ActionStepResult:
        """Execute single action using modular components"""
        try:
            # Use action executor to apply action effects
            success = self.action_executor.apply_action_effects(action_name, parameters)
            
            if success:
                # Do not execute inference in this module, maintain module decoupling
                # Inference functionality is handled by the main file
                
                # Use world state manager to validate world state
                validation_result = self.world_state_manager.validate_world_state(step_num, original_action)
                
                # Print detailed world state (for testing and debugging)
                self.world_state_manager.print_detailed_world_state(step_num, original_action)
                
                # Create world state snapshot (preparing for future multithreading)
                world_snapshot = self.world_state_manager.clone_world_state()
                
                # Skip safety detection, user only needs action inference
                hazards = []
                
                print(f"✅ Action execution successful")
                
                return ActionStepResult(
                    step_number=step_num,
                    action=original_action,
                    parameters=parameters,
                    success=True,
                    hazards=hazards,
                    errors=[],
                    world_state_after=self.world_state_manager.capture_world_state(),
                    validation_result=validation_result,
                    world_snapshot=world_snapshot
                )
            else:
                return ActionStepResult(
                    step_number=step_num,
                    action=original_action,
                    parameters=parameters,
                    success=False,
                    hazards=[],
                    errors=['Action execution failed'],
                    world_state_after=self.world_state_manager.capture_world_state()
                )
                
        except Exception as e:
            print(f"❌ Action execution error: {e}")
            return ActionStepResult(
                step_number=step_num,
                action=original_action,
                parameters=parameters,
                success=False,
                hazards=[],
                errors=[str(e)],
                world_state_after=self.world_state_manager.capture_world_state()
            )
