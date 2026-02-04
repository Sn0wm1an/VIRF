import owlready2 as owl
from typing import List, Dict, Any
from .safety_verifier import SafetyVerifier
from ..src.ontology_loader import OntologyLoader
from ..src.abox_tbox_mapper import ABoxTBoxMapper
from ..src.state_world.world_state_manager import WorldStateManager
from ..src.structured_output import create_hazard_feedback_details


class SequenceSafetyVerifier:
    """World state sequence safety verifier"""
    
    def __init__(self, world, verbose: bool = False):
        """
        Initialize sequence safety verifier
        
        Args:
            world: Owlready2 world instance
            verbose: Whether to enable detailed logging
        """
        self.world = world
        self.verbose = verbose
        self.world_state_manager = WorldStateManager(world, verbose=verbose)
    
    def verify_sequence_safety(self, state_sequence, plan_id: str) -> (bool, Dict[str, Any]):
        """
        Verify safety of world state sequence, collecting all hazards from all steps
        
        Args:
            state_sequence: World state snapshot sequence
            plan_id: Unique plan ID
            
        Returns:
            (is_safe, report): Tuple containing boolean value and hazard report dictionary
        """
        if self.verbose:
            print(f"\n🛡️ Starting full sequence safety verification (Plan ID: {plan_id})...")
            print(f"📋 States to verify: {len(state_sequence)}")
            
        all_dangerous_steps = []
        reported_hazard_keys = set()  # Track reported hazards

        for state in state_sequence:
            # Check all states, including initial state (step 0), as it may contain WARNING
            
            if self.verbose:
                print(f"\n   🔍 Verifying step {state.step_number}: {state.action_applied}")
            
            # Perform safety check on current state
            safety_result = self._verify_single_state(state)
            
            # If dangers, warnings, or unknown states are found in current step
            has_issues = (safety_result['is_dangerous'] or 
                         safety_result.get('status') in ['WARNING', 'DANGER', 'UNKNOWN'] or
                         safety_result.get('hazard_count', 0) > 0)
            
            if has_issues:
                if self.verbose:
                    print(f"   🚨 Found {safety_result.get('hazard_count', 0)} hazard(s)!")
                
                step_hazards = []
                # Iterate through all hazards in current step
                for hazard in safety_result['hazards']:
                    # Generate unique hazard key (rule ID + triggering instance)
                    rule_id = hazard.get('violated_rule', {}).get('id', 'UnknownRule')
                    
                    # Try to get subject instance from causal chain
                    facts = hazard.get('causal_chain', {}).get('triggering_facts', [])
                    subject = facts[0]['subject'] if facts else 'UnknownSubject'
                    
                    hazard_key = (rule_id, subject)

                    # If this hazard hasn't been reported yet
                    if hazard_key not in reported_hazard_keys:
                        feedback = create_hazard_feedback_details(
                            action_info_str=state.action_applied,
                            hazard_details=hazard
                        )
                        step_hazards.append(feedback)
                        reported_hazard_keys.add(hazard_key)  # Mark as reported
                
                # Only record this step if new, unreported hazards are found
                if step_hazards:
                    # Check if it's a preemptively detected hazard (by checking hazard instance names)
                    # If hazard involves next step action (like pour_instance), adjust display info
                    reported_step_number = state.step_number
                    reported_action = state.action_applied
                    
                    # Check if hazard involves next step action instance
                    for hazard in step_hazards:
                        facts = hazard.get('feedback_details', {}).get('causal_chain', {}).get('triggering_facts', [])
                        for fact in facts:
                            subject = fact.get('subject', '')
                            # If hazard instance is next step action instance (like pour_instance), adjust report info
                            if 'pour_instance' in subject:
                                reported_step_number = state.step_number + 1
                                reported_action = "pour"
                                break
                            elif 'throw_instance' in subject:
                                reported_step_number = state.step_number + 1
                                reported_action = "throw"
                                break
                            elif 'slice_instance' in subject:
                                reported_step_number = state.step_number + 1
                                reported_action = "slice"
                                break
                            elif 'break_instance' in subject:
                                reported_step_number = state.step_number + 1
                                reported_action = "break"
                                break
                            elif 'dirty_instance' in subject:
                                reported_step_number = state.step_number + 1
                                reported_action = "dirty"
                                break
                            elif 'drop_instance' in subject:
                                reported_step_number = state.step_number + 1
                                reported_action = "drop"
                                break
                    
                    all_dangerous_steps.append({
                        "step_number": reported_step_number,
                        "action_applied": reported_action,
                        "hazards": step_hazards
                    })
            else:
                if self.verbose:
                    print(f"   ✅ Step safe")

        # After loop ends, check if any hazards or warnings were collected
        if all_dangerous_steps:
            # Classify hazards: separate UNKNOWN, WARNING types (LogicalInconsistency) and UNSAFE types
            warning_steps = []
            unsafe_steps = []
            unknown_steps = []
            
            for step in all_dangerous_steps:
                step_hazards = []
                has_unsafe_hazards = False
                has_unknown_hazards = False
                
                for hazard in step.get('hazards', []):
                    # Check multiple locations to identify different types of rules
                    is_logical_inconsistency = False
                    is_unknown_material = False
                    
                    # 1. Check violated_rule.id (preferentially get from feedback_details)
                    feedback_details = hazard.get('feedback_details', {})
                    if feedback_details and 'violated_rule' in feedback_details:
                        violated_rule = feedback_details.get('violated_rule', {})
                    else:
                        violated_rule = hazard.get('violated_rule', {})
                    
                    rule_id = violated_rule.get('id', '')
                    if 'LogicalInconsistency' in rule_id:
                        is_logical_inconsistency = True
                    elif self._is_unknown_material_rule(rule_id):
                        is_unknown_material = True
                    
                    # 2. Check violated_rule.id in feedback_details
                    feedback_details = hazard.get('feedback_details', {})
                    if feedback_details:
                        fb_violated_rule = feedback_details.get('violated_rule', {})
                        fb_rule_id = fb_violated_rule.get('id', '')
                        if 'LogicalInconsistency' in fb_rule_id:
                            is_logical_inconsistency = True
                        elif self._is_unknown_material_rule(fb_rule_id):
                            is_unknown_material = True
                    
                    # 3. Check if hazard content contains any UnknownMaterial subclasses
                    if not is_unknown_material:
                        try:
                            unknown_material_classes = self._get_unknown_material_subclasses()
                            hazard_str = str(hazard)
                            for class_name in unknown_material_classes:
                                if class_name in hazard_str:
                                    is_unknown_material = True
                                    break
                        except Exception as e:
                            if self.verbose:
                                print(f"   ⚠️  Error checking UnknownMaterial subclasses in hazard: {e}")
                            # Fallback to basic check
                            if 'UnknownMaterial' in str(hazard):
                                is_unknown_material = True
                    
                    step_hazards.append(hazard)
                    
                    # Classify hazard types
                    if is_unknown_material:
                        has_unknown_hazards = True
                    elif not is_logical_inconsistency:
                        has_unsafe_hazards = True
                
                # Determine step category based on hazard type - Priority: UNKNOWN > UNSAFE > WARNING
                step_data = {
                    "step_number": step["step_number"],
                    "action_applied": step["action_applied"],
                    "hazards": step_hazards
                }
                
                if has_unknown_hazards:
                    unknown_steps.append(step_data)
                elif has_unsafe_hazards:
                    unsafe_steps.append(step_data)
                else:
                    warning_steps.append(step_data)
            
            # Priority: UNKNOWN > UNSAFE > WARNING
            if unknown_steps:
                # If there are UNKNOWN type hazards, report UNKNOWN
                final_report = {
                    "status": "UNKNOWN",
                    "violated_plan_id": plan_id,
                    "dangerous_steps": unknown_steps
                }
                return False, final_report
            elif unsafe_steps:
                # If there are UNSAFE type hazards, report UNSAFE (ignore WARNING)
                final_report = {
                    "status": "UNSAFE",
                    "violated_plan_id": plan_id,
                    "dangerous_steps": unsafe_steps  # Only include UNSAFE steps
                }
                return False, final_report
            elif warning_steps:
                # When only WARNING types exist, report WARNING
                final_report = {
                    "status": "WARNING", 
                    "violated_plan_id": plan_id,
                    "dangerous_steps": warning_steps
                }
                return True, final_report
        
        # If no hazards are found
        
        # Return safe report instead of None
        safe_report = {
            "status": "SAFE",
            "plan_id": plan_id,
            "total_steps": len([s for s in state_sequence if s.step_number > 0]),
            "message": "All steps passed safety verification"
        }
        
        return True, safe_report
    
    def _reconstruct_world_from_snapshot(self, world_snapshot: Dict[str, Any]) -> Any:
        """Reconstruct world state from snapshot"""
        try:
            # Use the centralized reconstruction logic from WorldStateManager
            reconstructed_data = self.world_state_manager.reconstruct_world_from_snapshot(world_snapshot)
            
            if not reconstructed_data:
                print(f"   ⚠️  State reconstruction failed: WorldStateManager.reconstruct_world_from_snapshot returned None")
                return None

            return reconstructed_data

        except Exception as e:
            print(f"   ❌ State reconstruction exception: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _verify_single_state(self, state) -> Dict[str, Any]:
        """
        Verify safety of a single state
        
        Args:
            state: World state snapshot
            
        Returns:
            Safety verification result for single state
        """
        # 🔑 Prioritize using safety verification results from reasoning copy
        if (hasattr(state, 'reasoning_result') and 
            state.reasoning_result and 
            'safety_verification' in state.reasoning_result):
            
            safety_result = state.reasoning_result['safety_verification']
            if self.verbose:
                print(f"   📦 Using safety verification results from reasoning copy")
            
            # Convert result format to maintain compatibility
            result = {
                'is_dangerous': not safety_result.get('is_safe', True),
                'hazard_count': len(safety_result.get('hazards', [])),
                'hazards': safety_result.get('hazards', []),
                'message': safety_result.get('message', ''),
                'status': safety_result.get('status', 'SAFE')
            }
            
            return result
        
        # Fallback to original logic: rebuild world state and verify
        if self.verbose:
            print(f"   🔄 No safety verification results in reasoning copy, falling back to world reconstruction verification")
            
        reconstructed_world_data = self._reconstruct_world_from_snapshot(state.world_snapshot)
        if not reconstructed_world_data:
            return {'is_dangerous': False, 'message': 'World state reconstruction failed'}

        temp_world, temp_onto = reconstructed_world_data
        
        try:
            # Create new safety verifier using reconstructed world
            temp_verifier = SafetyVerifier(external_world=temp_world, external_onto=temp_onto, verbose=self.verbose)
            safety_result = temp_verifier.check_safety()
            
            # Convert result format
            result = {
                'is_dangerous': not safety_result['is_safe'],
                'hazard_count': safety_result['hazard_count'],
                'hazards': safety_result['hazards'],
                'message': safety_result.get('message', '')
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ Single state verification failed: {e}")
            return {
                'is_dangerous': False,
                'hazard_count': 0,
                'hazards': [],
                'message': f"Verification failed: {e}"
            }
    
    
    def export_verification_report(self, report: Dict[str, Any], output_file: str) -> None:
        """Export structured hazard report to JSON file"""
        import json
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception as e:
            if self.verbose:
                print(f"📄 Hazard report export failed: {e}")
    
    def _is_unknown_material_rule(self, rule_id: str) -> bool:
        """
        Check if rule ID is UnknownMaterial related rule
        
        Args:
            rule_id: Rule ID
            
        Returns:
            Whether it's UnknownMaterial related rule
        """
        if not rule_id:
            return False
            
        # Basic UNKNOWN_MATERIAL_RULE
        if rule_id == 'UNKNOWN_MATERIAL_RULE':
            return True
            
        # Dynamically get all UnknownMaterial subclasses from ontology
        try:
            unknown_material_classes = self._get_unknown_material_subclasses()
            
            # Check if rule_id matches any UnknownMaterial subclass
            for class_name in unknown_material_classes:
                if class_name in rule_id:
                    return True
                    
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Error getting UnknownMaterial subclasses: {e}")
            
        # Fallback to basic pattern matching
        return 'UnknownMaterial' in rule_id
    
    def _get_unknown_material_subclasses(self) -> List[str]:
        """
        Dynamically get all subclasses inheriting from UnknownMaterial from ontology
        
        Returns:
            List of UnknownMaterial subclass names
        """
        unknown_material_classes = set()  # Use set to avoid duplicates
        
        try:
            # Try to get ontology from world_state_manager
            if hasattr(self, 'world_state_manager') and self.world_state_manager:
                ontology = self.world_state_manager.ontology
                
                if ontology:
                    # First find UnknownMaterial base class
                    unknown_material_base = None
                    for cls in ontology.classes():
                        if hasattr(cls, 'name') and cls.name:
                            # Match full class name or simplified class name
                            if (cls.name == 'UnknownMaterial' or 
                                cls.name.endswith('#UnknownMaterial') or 
                                cls.name.endswith('UnknownMaterial')):
                                unknown_material_base = cls
                                unknown_material_classes.add(cls.name.split('#')[-1])  # Add simplified name
                                break
                    
                    # If base class is found, get all subclasses
                    if unknown_material_base:
                        # Get direct and indirect subclasses
                        def get_all_subclasses(base_cls, visited=None):
                            if visited is None:
                                visited = set()
                            
                            if base_cls in visited:
                                return
                            visited.add(base_cls)
                            
                            try:
                                # Get direct subclasses
                                for subclass in base_cls.subclasses():
                                    if hasattr(subclass, 'name') and subclass.name:
                                        class_name = subclass.name.split('#')[-1]  # Get simplified name
                                        unknown_material_classes.add(class_name)
                                        # Recursively get subclasses of subclasses
                                        get_all_subclasses(subclass, visited)
                            except Exception as e:
                                pass  # Simplified error handling
                        
                        get_all_subclasses(unknown_material_base)
                    
                    # Additional check: look for rdfs:subClassOf relations
                    for cls in ontology.classes():
                        if hasattr(cls, 'name') and cls.name:
                            try:
                                # Check if there's rdfs:subClassOf pointing to UnknownMaterial
                                for parent in cls.is_a:
                                    if hasattr(parent, 'name') and parent.name:
                                        parent_name = parent.name.split('#')[-1]
                                        if parent_name in unknown_material_classes:
                                            class_name = cls.name.split('#')[-1]
                                            unknown_material_classes.add(class_name)
                            except Exception as e:
                                pass  # Simplified error handling
                                
        except Exception as e:
            pass  # Simplified error handling
        
        # Convert to list and add basic UnknownMaterial variants
        result = list(unknown_material_classes)
        if 'UnknownMaterial' not in result:
            result.append('UnknownMaterial')
            
        return result
