"""
Independent reasoning validation module - supports multi-threading
Creates reasoning copies from world state snapshots and performs safety validation
"""

import copy
import time
from typing import Dict, Any, Optional, Tuple
from .world_state_manager import WorldStateManager
from .action_executor import ActionExecutor
from .action_semantics import parse_action_sequence


class ReasoningValidator:
    """Reasoning validator - responsible for OWL reasoning and hazard detection"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize reasoning validator
        
        Args:
            verbose: Whether to display detailed logs
        """
        self.verbose = verbose
        # Cache reasoning world and manager to avoid repeated creation
        self._cached_temp_world = None
        self._cached_temp_manager = None
    
    def validate_step_safety(self, 
                           world_snapshot: Dict[str, Any], 
                           step_num: int, 
                           action_str: str,
                           next_action_str: Optional[str] = None,
                           current_held_object: Optional[str] = None,
                           last_found_object: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Validate step safety (independent function, supports multi-threading)
        
        Args:
            world_snapshot: World state snapshot
            step_num: Step number
            action_str: Current action string
            next_action_str: Next action string (optional)
            current_held_object: Current held object
            last_found_object: Last found object
            
        Returns:
            (reasoning result, whether InterruptDangerousSituation is detected)
        """
        try:
            if self.verbose:
                thread_info = f"[Thread Independent Validation]"
                print(f"   🧠 {thread_info} Step {step_num} Reasoning Validation")
            
            # Reconstruct reasoning world based on snapshot
            reasoning_world = self._reconstruct_reasoning_world(world_snapshot)
            if not reasoning_world:
                return None, False
            
            # If there is a next action, create action instance for validation
            if next_action_str:
                if self.verbose:
                    print(f"   🎬 {thread_info} Creating next action instance: {next_action_str}")
                self._create_action_instance_for_validation(
                    reasoning_world, next_action_str, step_num + 1, 
                    current_held_object, last_found_object
                )
            else:
                if self.verbose:
                    print(f"   🧠 {thread_info} Verifying final step safety")
            
            # Perform reasoning validation
            reasoning_result = self._perform_reasoning_validation(
                reasoning_world, step_num, action_str
            )
            
            # Check for InterruptDangerousSituation
            has_interrupt_danger = self._check_interrupt_dangerous_situation(reasoning_result)
            
            if self.verbose:
                if has_interrupt_danger:
                    print(f"   🔍 {thread_info} InterruptDangerousSituation detected")
                else:
                    print(f"   ✅ {thread_info} Reasoning validation completed, no interrupt danger")
            
            return reasoning_result, has_interrupt_danger
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Reasoning validation failed: {e}")
            return None, False
    
    def _reconstruct_reasoning_world(self, world_snapshot: Dict[str, Any]):
        """
        Reconstruct reasoning world based on snapshot (using cache for performance optimization)
        
        Args:
            world_snapshot: World state snapshot
            
        Returns:
            Reconstructed reasoning world
        """
        try:
            if not world_snapshot:
                if self.verbose:
                    print(f"   ⚠️ Reasoning world reconstruction failed: snapshot is empty")
                return None
            
            # Initialize cached reasoning components (only once)
            if self._cached_temp_world is None or self._cached_temp_manager is None:
                if self.verbose:
                    print(f"   🔄 Initialize reasoning cache...")
                import owlready2 as owl
                self._cached_temp_world = owl.World()
                self._cached_temp_manager = WorldStateManager(self._cached_temp_world, verbose=False)
            
            # Use cached manager to reconstruct world
            reconstructed_data = self._cached_temp_manager.reconstruct_world_from_snapshot(world_snapshot)
            
            if reconstructed_data:
                reasoning_world, _ = reconstructed_data
                if self.verbose:
                    print(f"   🧠 Reasoning world reconstruction successful (using cache)")
                return reasoning_world
            else:
                if self.verbose:
                    print(f"   ⚠️ Reasoning world reconstruction failed")
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Reasoning world reconstruction exception: {e}")
            return None
    
    def _create_action_instance_for_validation(self, reasoning_world, action_str: str, step_num: int,
                                             current_held_object: str = None, last_found_object: str = None) -> bool:
        """
        Create action instance for validation in reasoning world
        
        Args:
            reasoning_world: Reasoning world instance
            action_str: Action string
            step_num: Step number
            current_held_object: Current held object
            last_found_object: Last found object
            
        Returns:
            Whether creation was successful
        """
        try:
            parsed_actions = parse_action_sequence([action_str])
            if not parsed_actions:
                return False
                
            action_name, parameters = parsed_actions[0]
            
            # Handle implicit parameters and placeholder replacement
            if action_name == 'put' and parameters.get('object') is None:
                if current_held_object:
                    parameters['object'] = current_held_object
                    if self.verbose:
                        print(f"🔄 put action using current held object: {current_held_object}")
            
            # Handle placeholder parameter replacement
            for key, value in parameters.items():
                if value == 'current_held_object':
                    if current_held_object:
                        parameters[key] = current_held_object
                        if self.verbose:
                            print(f"🔄 Replace parameter {key}: current_held_object -> {current_held_object}")
                    else:
                        if self.verbose:
                            print(f"⚠️ Cannot replace parameter {key}: current_held_object is empty")
                elif value == 'last_found_object':
                    if last_found_object:
                        parameters[key] = last_found_object
                        if self.verbose:
                            print(f"🔄 Replace parameter {key}: last_found_object -> {last_found_object}")
                    else:
                        if self.verbose:
                            print(f"⚠️ Cannot replace parameter {key}: last_found_object is empty")
            
            # Create action executor and create instance
            action_executor = ActionExecutor(reasoning_world, verbose=self.verbose)
            success = action_executor._create_action_instance(action_name, parameters)
            
            if self.verbose:
                if success:
                    print(f"   ✅ Reasoning validation action instance created successfully: {action_name}")
                else:
                    print(f"   ⚠️ Reasoning validation action instance creation failed: {action_name}")
            
            return success
            
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _perform_reasoning_validation(self, reasoning_world, step_num: int, action_str: str) -> Optional[Dict[str, Any]]:
        """
        Perform reasoning validation
        
        Args:
            reasoning_world: Reasoning world instance
            step_num: Step number
            action_str: Action string
            
        Returns:
            Reasoning result
        """
        try:
            import owlready2 as owl
            
            if self.verbose:
                print(f"   🧠 Step {step_num} reasoning...")
            
            # Record the number of individuals before reasoning
            individuals_before = len(list(reasoning_world.individuals()))
            
            # 🔑 Execute Pellet reasoning
            start_time = time.time()
            
            with reasoning_world:
                owl.sync_reasoner_pellet(
                    reasoning_world, 
                    infer_property_values=True,
                    infer_data_property_values=True
                )
            
            reasoning_time = time.time() - start_time
            
            # Record the number of individuals after reasoning
            individuals_after = len(list(reasoning_world.individuals()))
            new_inferences = individuals_after - individuals_before
            
            if self.verbose:
                print(f"   ✅ Reasoning completed (time: {reasoning_time:.3f}s, new instances: {new_inferences})")
            
            # After reasoning, use SafetyVerifier for safety verification
            if self.verbose:
                print(f"   🔍 Starting safety verification...")
                
            from ...verify.safety_verifier import SafetyVerifier
            
            # Create safety verifier instance (using reasoning world)
            safety_verifier = SafetyVerifier(
                external_world=reasoning_world,
                external_onto=None,
                verbose=self.verbose
            )
            
            # Execute safety verification (no longer perform reasoning, as it has already been completed)
            verification_result = safety_verifier.check_safety()
            
            if self.verbose:
                if verification_result:
                    is_safe = verification_result.get('is_safe', True)
                    hazard_count = verification_result.get('hazard_count', 0)
                    print(f"   🔍 Reasoning verification result: {'Safe' if is_safe else f'Detected {hazard_count} hazards'}")
                else:
                    print(f"   ⚠️ Reasoning verification result: No result")
            
            return {
                'step_number': step_num,
                'action': action_str,
                'reasoning_time_seconds': round(reasoning_time, 3),
                'individuals_before': individuals_before,
                'individuals_after': individuals_after,
                'new_inferences': new_inferences,
                'safety_verification': verification_result,
                'reasoning_instances': verification_result.get('reasoning_instances', []) if verification_result else [],
                'success': True,
                'errors': []
            }
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Reasoning validation execution exception: {e}")
            
            # If it is an inconsistency error, try to get the explanation
            if "inconsistent" in str(e).lower():
                if self.verbose:
                    print(f"   🔍 Detected ontology inconsistency, trying to explain...")
                self._explain_inconsistency(reasoning_world)
            
            return {
                'step_number': step_num,
                'action': action_str,
                'reasoning_time_seconds': 0,
                'success': False,
                'errors': [f"Reasoning validation failed: {str(e)}"],
                'safety_verification': {'is_safe': True, 'hazards': [], 'hazard_count': 0}
            }
    
    def _check_interrupt_dangerous_situation(self, reasoning_result: Optional[Dict[str, Any]]) -> bool:
        """
        Check if InterruptDangerousSituation is present
        
        Args:
            reasoning_result: Reasoning result
            
        Returns:
            Whether InterruptDangerousSituation is detected
        """
        try:
            if not reasoning_result:
                return False
            
            # Check if InterruptDangerousSituation is present in reasoning instances
            reasoning_instances = reasoning_result.get('reasoning_instances', [])
            
            for instance_data in reasoning_instances:
                instance_types = instance_data.get('types', [])
                for instance_type in instance_types:
                    # Check if InterruptDangerousSituation or contains Danger
                    if (instance_type == 'InterruptDangerousSituation' or 
                        'Danger' in instance_type):
                        if self.verbose:
                            print(f"   🚨 Interrupt dangerous situation detected: {instance_data.get('name', 'Unknown')} (type: {instance_type})")
                        return True
            
            # Check if any hazards are detected in the safety verification result
            safety_verification = reasoning_result.get('safety_verification', {})
            hazards = safety_verification.get('hazards', [])
            
            for hazard in hazards:
                if 'violated_rule' in hazard:
                    rule_id = hazard['violated_rule'].get('id', '')
                    if (rule_id == 'InterruptDangerousSituation' or
                        'Interrupt' in rule_id or
                        ('Danger' in rule_id and rule_id.endswith('Danger'))):
                        return True
            
            return False
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Interrupt dangerous situation check exception: {e}")
            return False
    
    def _explain_inconsistency(self, reasoning_world):
        """
        Explain the inconsistency of the reasoning world
        
        Args:
            reasoning_world: Reasoning world instance
        """
        try:
            import tempfile
            import subprocess
            import os
            
            if self.verbose:
                print(f"   🔍 Analyzing ontology inconsistency...")
            
            # Create temporary file to save current world state
            with tempfile.NamedTemporaryFile(mode='w', suffix='.owl', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            # Save world state to temporary OWL file
            reasoning_world.save(file=temp_file_path, format="rdfxml")
            
            # Use pellet explain command
            pellet_jar_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "verify", "pellet.jar")
            
            if os.path.exists(pellet_jar_path):
                result = subprocess.run([
                    "java", "-jar", pellet_jar_path, "explain", "--input-file", temp_file_path
                ], capture_output=True, text=True, timeout=60)
                
                if self.verbose:
                    print(f"   📄 Pellet explain output:")
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(f"   ⚠️ Error: {result.stderr}")
            
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Inconsistency analysis failed: {e}")
