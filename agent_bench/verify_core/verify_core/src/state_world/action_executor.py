"""
Action executor
Responsible for specific action semantic mapping and effect application
"""

from typing import Dict
import owlready2 as owl


class ActionExecutor:
    """Action executor"""
    
    def __init__(self, world: owl.World, verbose: bool = False):
        """
        Initialize action executor
        
        Args:
            world: OWL world instance
            verbose: Whether to enable detailed logging
        """
        self.world = world
        self.verbose = verbose
        # State tracking
        self.currently_holding = None  # Currently held object
        self.last_found_object = None  # Last found object
    
    def apply_action_effects(self, action_name: str, parameters: Dict[str, str]) -> bool:
        """Apply action effects according to user-defined action semantic rules"""
        try:
            # Handle placeholder parameter substitution
            for key, value in parameters.items():
                if value == 'current_held_object':
                    if self.currently_holding:
                        parameters[key] = self.currently_holding
                        if self.verbose:
                            print(f"   🔄 Replace parameter {key}: current_held_object -> {self.currently_holding}")
                    else:
                        if self.verbose:
                            print(f"   ⚠️ Cannot replace parameter {key}: current_held_object is empty")
                elif value == 'last_found_object':
                    if self.last_found_object:
                        parameters[key] = self.last_found_object
                        if self.verbose:
                            print(f"   🔄 Replace parameter {key}: last_found_object -> {self.last_found_object}")
                    else:
                        if self.verbose:
                            print(f"   ⚠️ Cannot replace parameter {key}: last_found_object is empty")
            
            with self.world:
                if action_name == "find":
                    return self._handle_find_action(parameters)
                elif action_name == "pick":
                    return self._handle_pick_action(parameters)
                elif action_name == "open":
                    return self._handle_open_action(parameters)
                elif action_name == "close":
                    return self._handle_close_action(parameters)
                elif action_name == "put":
                    return self._handle_put_action(parameters)
                elif action_name == "turn_on":
                    return self._handle_turn_on_action(parameters)
                elif action_name == "turn_off":
                    return self._handle_turn_off_action(parameters)
                elif action_name == "pour":
                    return self._handle_pour_action(parameters)
                elif action_name == "fillLiquid" or action_name == "fillliquid":
                    return self._handle_fill_liquid_action(parameters)
                elif action_name == "clean":
                    return self._handle_clean_action(parameters)
                elif action_name == "dirty":
                    return self._handle_dirty_action(parameters)
                elif action_name == "throw":
                    return self._handle_throw_action(parameters)
                elif action_name == "drop":
                    return self._handle_drop_action(parameters)
                elif action_name == "break":
                    return self._handle_break_action(parameters)
                elif action_name == "slice":
                    return self._handle_slice_action(parameters)
                elif action_name == "cook":
                    return self._handle_cook_action(parameters)
                else:
                    print(f"   ❌ Unknown action: {action_name}")
                    return False
            
        except Exception as e:
            print(f"   ❌ Apply action effects failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _handle_find_action(self, parameters: Dict[str, str]) -> bool:
        """Handle find action - find object and set its isLocated property to true"""
        obj_name = parameters.get("object")
        obj = self.world.search_one(iri=f"*{obj_name}")
        if not obj:
            print(f"   ❌ Cannot find object: {obj_name}")
            return False
        
        # Core effect of find action: change target object's isLocated property from false to true
        self._set_object_located(obj, obj_name)
        
        # Update last_found_object tracking
        self.last_found_object = obj_name
        
        if self.verbose:
            print(f"   🔍 Found object: {obj_name}")
        return True

    def _set_object_located(self, obj, obj_name: str):
        """Set object's isLocated property to true"""
        try:
            # Find isLocated property
            is_located_prop = self.world.search_one(iri="*isLocated")
            if is_located_prop:
                # Set isLocated property to true
                setattr(obj, is_located_prop.python_name, True)
                if self.verbose:
                    print(f"   🎯 Cognitive state update: {obj_name} is now considered 'located'")
            else:
                if self.verbose:
                    print(f"   ⚠️ isLocated property not found")
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Failed to set isLocated property: {e}")

    def _debug_target_object_islocated(self, obj, obj_name):
        """Debug target object's isLocated property state"""
        try:
            is_located_prop = self.world.search_one(iri="*isLocated")
            if is_located_prop:
                prop_value = getattr(obj, is_located_prop.python_name)
                print(f"   🔍 [PICK Debug] {obj_name}.isLocated = {prop_value} (type: {type(prop_value)})")
                
                if hasattr(prop_value, '__len__') and not isinstance(prop_value, str):
                    print(f"   🔍 [PICK Debug] List length: {len(prop_value)}")
                    if len(prop_value) > 0:
                        print(f"   🔍 [PICK Debug] First value: {prop_value[0]}")
                else:
                    print(f"   🔍 [PICK Debug] Direct value: {prop_value}")
            else:
                print(f"   ⚠️ [PICK Debug] isLocated property not found")
        except Exception as e:
            print(f"   ❌ [PICK Debug] Check isLocated failed: {e}")

    def _handle_pick_action(self, parameters) -> bool:
        """Handle pick action - pick up object, clear all spatial relations, establish holding relation"""
        obj_name = parameters.get("object")
        obj = self.world.search_one(iri=f"*{obj_name}")
        if not obj:
            print(f"   ❌ Cannot find object: {obj_name}")
            return False
            
        # Debug: check target object's isLocated property
        if self.verbose:
            self._debug_target_object_islocated(obj, obj_name)
            
        # Clear all spatial relations of this object
        self._clear_all_spatial_relations_from_object(obj, obj_name)
        
        # Find Agent or Robot to hold object, prioritize my_robot
        agent = None
        
        # Prioritize finding my_robot
        my_robot = self.world.search_one(iri="*my_robot")
        if my_robot:
            agent = my_robot
            if self.verbose:
                print(f"   🔍 Using default robot: {my_robot}")
        else:
            # If my_robot not found, try to find other Agent or Robot
            for individual in self.world.individuals():
                # Use safe type checking method to avoid Robot> issues
                type_name = ""
                if hasattr(type(individual), 'name'):
                    type_name = type(individual).name
                elif hasattr(type(individual), '__name__'):
                    type_name = type(individual).__name__
                
                if hasattr(individual, 'isHolding') or 'Agent' in type_name or 'Robot' in type_name:
                    agent = individual
                    if self.verbose:
                        print(f"   🔍 Using backup agent: {individual}")
                    break
        
        if not agent:
            if self.verbose:
                print(f"   ❌ Cannot find available agent to hold object")
            return False
        
        # =============== Set holding relation ===============
        self._establish_holding_relation(agent, obj, obj_name)
        
        # Record currently held object
        self.currently_holding = obj_name
        
        if self.verbose:
            print(f"   📦 Picked up: {obj_name}")
        return True
    
    def _handle_open_action(self, parameters: Dict[str, str]) -> bool:
        """Handle open action - use hasState attribute to set door open state"""
        obj_name = parameters.get("object")
        obj = self.world.search_one(iri=f"*{obj_name}")
        if not obj:
            if self.verbose:
                print(f"   ❌ Cannot find object to open: {obj_name}")
            return False
        
        # Find door state class and hasState attribute
        door_open_state = self.world.search_one(iri="*DoorOpenState")
        has_state_prop = self.world.search_one(iri="*hasState")
        
        # Create and set door open state
        if door_open_state and has_state_prop:
            # Create door open state instance
            open_instance_name = f"DoorOpenState_for_{obj_name}"
            try:
                with obj.namespace.ontology:
                    open_instance = door_open_state(open_instance_name)
                    # Clear previous states
                    if hasattr(obj, has_state_prop.python_name):
                        current_states = getattr(obj, has_state_prop.python_name)
                        if current_states:
                            current_states.clear()
                    # Set new state
                    getattr(obj, has_state_prop.python_name).append(open_instance)
                    if self.verbose:
                        print(f"   ✅ Set door open state: {obj_name}.hasState = DoorOpenState")
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️ Failed to set door open state: {e}")
        
        if self.verbose:
            print(f"   🚺 Opened {obj_name}")
        return True
    
    def _handle_close_action(self, parameters: Dict[str, str]) -> bool:
        """Handle close action - use hasState attribute to set door closed state"""
        obj_name = parameters.get("object")
        obj = self.world.search_one(iri=f"*{obj_name}")
        if not obj:
            if self.verbose:
                print(f"   ❌ Cannot find object to close: {obj_name}")
            return False
        
        # Find door state class and hasState attribute
        door_closed_state = self.world.search_one(iri="*DoorClosedState")
        has_state_prop = self.world.search_one(iri="*hasState")
        
        # Create and set door closed state
        if door_closed_state and has_state_prop:
            # Create door closed state instance
            closed_instance_name = f"DoorClosedState_for_{obj_name}"
            try:
                with obj.namespace.ontology:
                    closed_instance = door_closed_state(closed_instance_name)
                    # Clear previous states
                    if hasattr(obj, has_state_prop.python_name):
                        current_states = getattr(obj, has_state_prop.python_name)
                        if current_states:
                            current_states.clear()
                    # Set new state
                    getattr(obj, has_state_prop.python_name).append(closed_instance)
                    if self.verbose:
                        print(f"   ✅ Set door closed state: {obj_name}.hasState = DoorClosedState")
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️ Failed to set door closed state: {e}")
        
        if self.verbose:
            print(f"   🚺 Closed {obj_name}")
        return True
    
    def _handle_put_action(self, parameters: Dict[str, str]) -> bool:
        """Handle put action - put A in B or put A on B, supports automatic retrieval of robot-held objects"""
        obj_name = parameters.get("object")
        surface_name = parameters.get("surface")
        preposition = parameters.get("preposition", "on")  # Default to "on"
        
        # If obj_name is None, automatically get robot-held object
        if obj_name is None:
            obj = self._get_robot_held_object()
            if not obj:
                if self.verbose:
                    print(f"   ❌ Robot is currently not holding any object")
                return False
            obj_name = self._get_clean_name(obj)
            if self.verbose:
                print(f"   🎯 Automatically detected held object: {obj_name}")
        else:
            obj = self.world.search_one(iri=f"*{obj_name}")
            if not obj:
                if self.verbose:
                    print(f"   ❌ Cannot find object: {obj_name}")
                return False
        
        surface = self.world.search_one(iri=f"*{surface_name}")
        
        if not obj:
            if self.verbose:
                print(f"   ❌ Cannot find object: {obj_name}")
            return False
        if not surface:
            if self.verbose:
                print(f"   ❌ Cannot find surface/container: {surface_name}")
            return False
        
        if preposition == "in":
            # put A in B - B contain A
            contains_prop = self.world.search_one(iri="*contains")
            if self.verbose:
                print(f"   🔍 Search contains attribute result: {contains_prop}")
            if contains_prop:
                # contains attribute is not functional, need to use append
                if hasattr(surface, contains_prop.python_name):
                    getattr(surface, contains_prop.python_name).append(obj)
                    if self.verbose:
                        print(f"   ✅ Successfully created contains relation: {surface_name}.{contains_prop.python_name}.append({obj_name})")
                else:
                    setattr(surface, contains_prop.python_name, [obj])
                    if self.verbose:
                        print(f"   ✅ Successfully set contains relation: {surface_name}.{contains_prop.python_name} = [{obj_name}]")
            else:
                if self.verbose:
                    print(f"   ❌ Contains attribute not found, cannot create containment relation")
            if self.verbose:
                print(f"   📦 {obj_name} put into {surface_name}")
        else:  # "on" or other
            # put A on B - A is on top of B, establish bidirectional relation
            is_on_prop = self.world.search_one(iri="*isOn")
            is_at_prop = self.world.search_one(iri="*isAt")
            supports_prop = self.world.search_one(iri="*supports")
            
            if is_on_prop:
                # isOn is not a functional property, need to use list assignment
                if hasattr(obj, is_on_prop.python_name):
                    current_on = getattr(obj, is_on_prop.python_name)
                    if current_on:
                        current_on.clear()
                    current_on.append(surface)
                else:
                    setattr(obj, is_on_prop.python_name, [surface])
                    
                # 🔑 Key fix: create bidirectional relation B supports A
                if supports_prop:
                    if hasattr(surface, supports_prop.python_name):
                        getattr(surface, supports_prop.python_name).append(obj)
                    else:
                        setattr(surface, supports_prop.python_name, [obj])
                    if self.verbose:
                        print(f"   ✅ Created bidirectional relation: {surface_name}.supports = {obj_name}")
                        
            elif is_at_prop:
                # isAt also uses list assignment
                if hasattr(obj, is_at_prop.python_name):
                    current_at = getattr(obj, is_at_prop.python_name)
                    if current_at:
                        current_at.clear()
                    current_at.append(surface)
                else:
                    setattr(obj, is_at_prop.python_name, [surface])
            if self.verbose:
                print(f"   📦 {obj_name} placed on {surface_name}")
    
        # =============== Important: clear robot's holding state ===============
        # After put action, robot no longer holds the object
        self._clear_robot_holding_after_put(obj)
        
        return True
    
    def _get_robot_held_object(self):
        """Get currently held object by robot"""
        try:
            # Find default robot
            robot = self.world.search_one(iri="*my_robot")
            if not robot:
                if self.verbose:
                    print(f"   ⚠️ Robot not found")
                return None
            
            # Find isHolding attribute
            is_holding_prop = self.world.search_one(iri="*isHolding")
            if not is_holding_prop:
                if self.verbose:
                    print(f"   ⚠️ isHolding attribute not found")
                return None
            
            # Get list of objects currently held by robot
            holding_list = getattr(robot, is_holding_prop.python_name, [])
            
            if not holding_list:
                return None
            
            # Return first held object (usually robot can only hold one object at a time)
            return holding_list[0]
                
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Failed to get robot held object: {e}")
            return None
    
    def _get_clean_name(self, obj):
        """Get clean name of object, handle FusionClass issues"""
        if hasattr(obj, 'name'):
            return obj.name
        elif hasattr(obj, '__name__'):
            return obj.__name__
        else:
            return str(obj)

    def _create_action_instance(self, action_name: str, parameters: Dict[str, str]) -> bool:
        """Create action instance in ontology"""
        try:
            if self.verbose:
                print(f"   🎭 Creating action instance: {action_name} with {parameters}")
            
            # Find action class
            action_class = None
            # Special mapping rules
            action_name_mapping = {
                'pick': 'PickUpAction',
                'fillLiquid': 'FillLiquidAction',
                'pour': 'PourAction',
                'find': 'FindAction',
                'put': 'PutAction',
                'open': 'OpenAction',
                'close': 'CloseAction',
                'turn_on': 'ToggleOnAction',
                'turn_off': 'ToggleOffAction',
                'slice': 'SliceAction',
                'break': 'BreakAction',
                'drop': 'DropAction',
                'throw': 'ThrowAction',
                'clean': 'CleanAction',
                'dirty': 'DirtyAction'
            }
            
            if action_name in action_name_mapping:
                possible_action_names = [action_name_mapping[action_name]]
            else:
                possible_action_names = [
                    f"{action_name.capitalize()}Action",
                    f"{action_name.capitalize()}",
                    f"{action_name}Action",
                    action_name
                ]
            
            for possible_name in possible_action_names:
                action_class = self.world.search_one(iri=f"*{possible_name}")
                if action_class:
                    if self.verbose:
                        print(f"   ✅ Found action class: {possible_name}")
                    break
            
            if not action_class:
                if self.verbose:
                    print(f"   ⚠️ Action class not found: {action_name}")
                return True  # Don't affect subsequent flow
            
            # Create action instance
            instance_name = f"{action_name}_instance_{len(list(self.world.individuals()))}"
            action_instance = action_class(instance_name)
            
            # Set action parameters - use hasTarget relation
            # Special handling for pour action: hasTarget only points to target parameter
            if action_name == 'pour':
                target_value = parameters.get('target')
                if target_value:
                    try:
                        param_obj = self.world.search_one(iri=f"*{target_value}")
                        if param_obj:
                            # Create relation: ActionInstance hasTarget TargetObject
                            if hasattr(action_instance, 'hasTarget'):
                                action_instance.hasTarget.append(param_obj)
                            else:
                                action_instance.hasTarget = [param_obj]
                            
                            if self.verbose:
                                print(f"   ✅ Created relation: {action_instance.name} hasTarget {target_value}")
                        else:
                            if self.verbose:
                                print(f"   ⚠️ Target object not found: {target_value}")
                    except Exception as e:
                        if self.verbose:
                            print(f"   ⚠️ Failed to create hasTarget relation: target = {target_value}, {e}")
            else:
                # Other actions: create hasTarget relations for parameters except agent and preposition
                for param_key, param_value in parameters.items():
                    if param_key in ['agent', 'preposition']:  # Skip agent and preposition parameters
                        continue
                    try:
                        # Find object corresponding to parameter value
                        param_obj = self.world.search_one(iri=f"*{param_value}")
                        if param_obj:
                            # Create relation: ActionInstance hasTarget TargetObject
                            if hasattr(action_instance, 'hasTarget'):
                                action_instance.hasTarget.append(param_obj)
                            else:
                                action_instance.hasTarget = [param_obj]
                            
                            if self.verbose:
                                print(f"   ✅ Created relation: {action_instance.name} hasTarget {param_value}")
                        else:
                            if self.verbose:
                                print(f"   ⚠️ Target object not found: {param_value}")
                    except Exception as e:
                        if self.verbose:
                            print(f"   ⚠️ Failed to create hasTarget relation: {param_key} = {param_value}, {e}")
            
            if self.verbose:
                print(f"   ✅ Action instance created successfully: {instance_name}")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Failed to create action instance: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _clear_robot_holding_after_put(self, put_object):
        """Clear robot's holding state after put action"""
        try:
            # Find default robot
            robot = self.world.search_one(iri="*my_robot")
            if not robot:
                if self.verbose:
                    print(f"   ⚠️ Robot not found, cannot clear holding state")
                return
            
            # Find isHolding property
            is_holding_prop = self.world.search_one(iri="*isHolding")
            if not is_holding_prop:
                if self.verbose:
                    print(f"   ⚠️ isHolding property not found")
                return
            
            # Get robot's current holding list
            holding_list = getattr(robot, is_holding_prop.python_name, [])
            
            # Remove put down object from holding list
            if put_object in holding_list:
                holding_list.remove(put_object)
                if self.verbose:
                    print(f"   🤖 Robot no longer holding: {put_object}")
            
            # Update handIsEmpty state
            hand_is_empty_prop = self.world.search_one(iri="*handIsEmpty")
            if hand_is_empty_prop:
                # If holding list is empty, set hand as empty
                is_empty = len(holding_list) == 0
                setattr(robot, hand_is_empty_prop.python_name, [is_empty])
                if self.verbose:
                    print(f"   ✋ Robot hand state: {'empty' if is_empty else 'not empty'}")
                
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Failed to clear robot holding state: {e}")

    def _handle_turn_on_action(self, parameters: Dict[str, str]) -> bool:
        """Handle turn_on action - associated with OnState/OffState, set to on state
        Special handling: if turning on StoveKnob or StoveBurner, set OnState for both simultaneously"""
        obj_name = parameters.get("object")
        obj = self.world.search_one(iri=f"*{obj_name}")
        if not obj:
            if self.verbose:
                print(f"   ❌ Cannot find device to turn on: {obj_name}")
            return False
        
        # Check if it's StoveKnob or StoveBurner, implement state synchronization
        is_stove_related = self._is_stove_component(obj)
        
        if is_stove_related:
            # StoveKnob/StoveBurner special handling: turn on related components simultaneously
            return self._handle_stove_turn_on(obj_name, obj)
        else:
            # Regular device turn on handling
            return self._set_device_on_state(obj, obj_name)
    
    def _is_stove_component(self, obj) -> bool:
        """Check if object is stove-related component (StoveKnob or StoveBurner)"""
        try:
            obj_type = type(obj).__name__
            return 'StoveKnob' in obj_type or 'StoveBurner' in obj_type
        except:
            return False
    
    def _handle_stove_turn_on(self, obj_name: str, obj) -> bool:
        """Handle stove component turn on, ensure StoveKnob and StoveBurner state synchronization"""
        if self.verbose:
            print(f"   🔥 Detected stove component, executing state synchronization: {obj_name}")
        
        # 1. Turn on current device
        success = self._set_device_on_state(obj, obj_name)
        if not success:
            return False
        
        # 2. Find and simultaneously turn on related stove components
        try:
            # Find all StoveKnob and StoveBurner instances
            stove_knobs = []
            stove_burners = []
            
            for individual in self.world.individuals():
                try:
                    obj_type = type(individual).__name__
                    if 'StoveKnob' in obj_type:
                        stove_knobs.append(individual)
                    elif 'StoveBurner' in obj_type:
                        stove_burners.append(individual)
                except:
                    continue
            
            # Turn on all StoveKnob and StoveBurner simultaneously (achieve complete synchronization)
            synced_devices = []
            
            for knob in stove_knobs:
                if knob != obj:  # Avoid duplicate processing of current device
                    if self._set_device_on_state(knob, knob.name):
                        synced_devices.append(knob.name)
            
            for burner in stove_burners:
                if burner != obj:  # Avoid duplicate processing of current device
                    if self._set_device_on_state(burner, burner.name):
                        synced_devices.append(burner.name)
            
            if synced_devices and self.verbose:
                print(f"   ✅ State synchronization completed, turned on simultaneously: {', '.join(synced_devices)}")
                
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Stove state synchronization partially failed: {e}")
            return True  # Main device already turned on, return success
    
    def _set_device_on_state(self, obj, obj_name: str) -> bool:
        """Set device's OnState status"""
        try:
            # Find OnState class and related properties
            on_state_class = self.world.search_one(iri="*OnState")
            has_state_prop = self.world.search_one(iri="*hasState")
            is_operating_prop = self.world.search_one(iri="*isOperating")
            
            if on_state_class and has_state_prop:
                # Create OnState instance instead of using class
                on_state_instance = on_state_class()
                # hasState property is not functional, need to use append or list assignment
                if hasattr(obj, has_state_prop.python_name):
                    current_states = getattr(obj, has_state_prop.python_name)
                    if current_states:
                        current_states.clear()
                    current_states.append(on_state_instance)
                else:
                    setattr(obj, has_state_prop.python_name, [on_state_instance])
                
                if self.verbose:
                    print(f"   ✅ Set OnState: {obj_name}")
                    
            if is_operating_prop:
                # isOperating property may need boolean value or state individual, try boolean value first
                try:
                    setattr(obj, is_operating_prop.python_name, True)
                except (ValueError, AttributeError):
                    # If boolean value doesn't work, try to find or create operating state individual
                    operating_state = self.world.search_one(iri="*OperatingState")
                    if operating_state:
                        if hasattr(obj, is_operating_prop.python_name):
                            getattr(obj, is_operating_prop.python_name).append(operating_state)
                        else:
                            setattr(obj, is_operating_prop.python_name, [operating_state])
                    else:
                        # If OperatingState not found, skip isOperating setting
                        if self.verbose:
                            print(f"   ⚠️ OperatingState not found, skipping isOperating setting")
            
            if self.verbose:
                print(f"   🔌 Turned on {obj_name}")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Failed to set device OnState: {obj_name}, {e}")
            return False
    
    def _handle_turn_off_action(self, parameters: Dict[str, str]) -> bool:
        """Handle turn_off action - associated with OnState/OffState, set to off state"""
        obj_name = parameters.get("object")
        obj = self.world.search_one(iri=f"*{obj_name}")
        if not obj:
            if self.verbose:
                print(f"   ❌ Cannot find device to turn off: {obj_name}")
            return False
        
        # Find OffState and related properties
        off_state = self.world.search_one(iri="*OffState")
        has_state_prop = self.world.search_one(iri="*hasState")
        is_operating_prop = self.world.search_one(iri="*isOperating")
        
        if off_state and has_state_prop:
            # hasState property is not functional, need to use append or list assignment
            if hasattr(obj, has_state_prop.python_name):
                current_states = getattr(obj, has_state_prop.python_name)
                if current_states:
                    current_states.clear()
                current_states.append(off_state)
            else:
                setattr(obj, has_state_prop.python_name, [off_state])
        if is_operating_prop:
            # Remove operating state or set to False
            try:
                # Try to clear property first
                if hasattr(obj, is_operating_prop.python_name):
                    current_operating = getattr(obj, is_operating_prop.python_name)
                    if hasattr(current_operating, 'clear'):
                        current_operating.clear()
                    else:
                        delattr(obj, is_operating_prop.python_name)
            except:
                # If clearing fails, try to set to False or non-operating state
                try:
                    setattr(obj, is_operating_prop.python_name, False)
                except (ValueError, AttributeError):
                    # If boolean value doesn't work, try to find non-operating state
                    non_operating_state = self.world.search_one(iri="*NonOperatingState")
                    if non_operating_state:
                        if hasattr(obj, is_operating_prop.python_name):
                            current_states = getattr(obj, is_operating_prop.python_name)
                            if current_states:
                                current_states.clear()
                            current_states.append(non_operating_state)
                        else:
                            setattr(obj, is_operating_prop.python_name, [non_operating_state])
                    else:
                        if self.verbose:
                            print(f"   ⚠️ NonOperatingState not found, skipping isOperating setting")
        
        if self.verbose:
            print(f"   🔌 Turned off {obj_name}")
        return True
    
    def _clear_all_spatial_relations_from_object(self, obj, obj_name: str):
        """Helper method: clear all spatial relations of object (when being picked up)"""
        if self.verbose:
            print(f"   🧹 Clearing all spatial relations of {obj_name}...")
        
        # Define list of spatial relation properties to clear (excluding contains, retain internal contents when picking up containers)
        spatial_properties = [
            'isOn', 'isInside', 'isAbove', 'touches', 'isNear', 'isAt',
            'isConnectedTo', 'supports', 'isAdjacentTo'
        ]
        
        # Clear spatial properties one by one
        for prop_name in spatial_properties:
            try:
                prop = self.world.search_one(iri=f"*{prop_name}")
                if prop and hasattr(obj, prop.python_name):
                    current_relations = getattr(obj, prop.python_name)
                    if current_relations:
                        current_relations.clear()
            except Exception as e:
                pass
        
        # Reverse relation clearing: remove relations pointing to this object from other objects
        # Special handling: if picked object is a container, don't remove container from internal liquid's isInside
        try:
            # First check if picked object is a container (has contains relation)
            is_container = False
            contains_prop = self.world.search_one(iri="*contains")
            if contains_prop and hasattr(obj, contains_prop.python_name):
                contains_attr = getattr(obj, contains_prop.python_name)
                if contains_attr:
                    is_container = True
            
            for individual in self.world.individuals():
                if individual == obj:
                    continue
                    
                # Check if other objects have spatial relations pointing to this object
                for prop_name in spatial_properties:
                    try:
                        prop = self.world.search_one(iri=f"*{prop_name}")
                        if prop and hasattr(individual, prop.python_name):
                            current_relations = getattr(individual, prop.python_name)
                            if current_relations and obj in current_relations:
                                # Special check: if container is picked up, don't remove container from liquid's isInside
                                if is_container and prop_name == 'isInside':
                                    liquid_class = self.world.search_one(iri="*Liquid")
                                    if liquid_class and isinstance(individual, liquid_class):
                                        continue
                                
                                current_relations.remove(obj)
                    except Exception as e:
                        pass
        except Exception as e:
            pass
    
    def _establish_holding_relation(self, agent, obj, obj_name: str):
        """Helper method: establish agent holding object relation"""
        try:
            # Set isHolding relation
            if hasattr(agent, 'isHolding'):
                current_holding = getattr(agent, 'isHolding')
                if current_holding:
                    current_holding.clear()
                current_holding.append(obj)
                if self.verbose:
                    print(f"   ✅ Set holding relation: agent.isHolding = {obj_name}")
            
            # Set isConnectedTo relation (bidirectional)
            is_connected_prop = self.world.search_one(iri="*isConnectedTo")
            if is_connected_prop:
                # Agent connects to Object
                if hasattr(agent, is_connected_prop.python_name):
                    agent_connections = getattr(agent, is_connected_prop.python_name)
                    if obj not in agent_connections:
                        agent_connections.append(obj)
                        if self.verbose:
                            print(f"   ✅ Set connection relation: agent.isConnectedTo = {obj_name}")
                
                # Object connects to Agent
                if hasattr(obj, is_connected_prop.python_name):
                    obj_connections = getattr(obj, is_connected_prop.python_name)
                    obj_connections.clear()  # Clear previous connections
                    obj_connections.append(agent)
                    if self.verbose:
                        print(f"   ✅ Set reverse connection: {obj_name}.isConnectedTo = agent")
            
            # Update hand status
            if hasattr(agent, 'handIsEmpty'):
                try:
                    hand_empty_attr = getattr(agent, 'handIsEmpty')
                    if isinstance(hand_empty_attr, list):
                        hand_empty_attr.clear()
                        hand_empty_attr.append(False)
                    else:
                        setattr(agent, 'handIsEmpty', [False])
                    if self.verbose:
                        print(f"   ✅ Update hand status: handIsEmpty = False")
                except Exception as e:
                    if self.verbose:
                        print(f"   ⚠️ Failed to update hand status: {e}")
                        
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Failed to establish holding relation: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_pour_action(self, parameters: Dict[str, str]) -> bool:
        """
        Handle pour action - pour liquid from source container to target container
        
        Rules:
        - Established relations: Liquid isInside TargetContainer, TargetContainer contains Liquid
        - Removed relations: Liquid isInside SourceContainer, SourceContainer contains Liquid  
        - Process relations: SourceContainer isAbove TargetContainer (during pouring process)
        
        Special logic: If no liquid is explicitly specified, automatically search for liquid in source container
        """
        try:
            source_name = parameters.get("source")  # Source container
            target_name = parameters.get("target")  # Target container
            liquid_name = parameters.get("object")  # Liquid (optional)
            
            # Handle magic strings and automatic state inference
            if source_name == "current_held_object":
                source_name = self.currently_holding
                if self.verbose:
                    print(f"   📦 Using currently held item as source container: {source_name}")
            elif not source_name and self.currently_holding:
                source_name = self.currently_holding
                if self.verbose:
                    print(f"   📦 Automatically using currently held item as source container: {source_name}")
            
            if target_name == "last_found_object":
                target_name = self.last_found_object
                if self.verbose:
                    print(f"   🎯 Using last found object as target: {target_name}")
            elif not target_name and self.last_found_object:
                target_name = self.last_found_object
                if self.verbose:
                    print(f"   🎯 Automatically using last found object as target: {target_name}")
            
            if not all([source_name, target_name]):
                print(f"   ❌ pour action parameters incomplete: source={source_name}, target={target_name}")
                print(f"   💡 Tip: Make sure to execute pick(hold source container) and find(find target) before pour")
                return False
            
            # Find source container and target container
            source_container = self.world.search_one(iri=f"*{source_name}")
            target_container = self.world.search_one(iri=f"*{target_name}")
            
            if not source_container:
                print(f"   ❌ Cannot find source container: {source_name}")
                return False
            if not target_container:
                print(f"   ❌ Cannot find target container: {target_name}")
                return False
            
            # If no liquid specified, search from source container
            liquid = None
            if liquid_name:
                liquid = self.world.search_one(iri=f"*{liquid_name}")
            else:
                # Automatically search for liquid in source container
                contains_prop = self.world.search_one(iri="*contains")
                if contains_prop and hasattr(source_container, contains_prop.python_name):
                    source_contents = getattr(source_container, contains_prop.python_name)
                
                    if isinstance(source_contents, list):
                        for item in source_contents:
                            # Check if it's a liquid instance
                            liquid_class = self.world.search_one(iri="*Liquid")
                            if liquid_class and isinstance(item, liquid_class):
                                liquid = item
                                liquid_name = str(item)
                                if self.verbose:
                                    print(f"   ✅ Found liquid: {liquid_name}")
                                break
                    elif source_contents:
                        # Single content item
                        liquid_class = self.world.search_one(iri="*Liquid")
                        if liquid_class and isinstance(source_contents, liquid_class):
                            liquid = source_contents
                            liquid_name = str(source_contents)
                            if self.verbose:
                                print(f"   ✅ Found liquid: {liquid_name}")
            
            if not liquid:
                print(f"   ❌ No liquid found in source container {source_name}")
                return False
            
            # Remove relations between source container and liquid
            # 1. Remove Liquid isInside SourceContainer
            is_inside_prop = self.world.search_one(iri="*isInside")
            if is_inside_prop and hasattr(liquid, is_inside_prop.python_name):
                liquid_inside_attr = getattr(liquid, is_inside_prop.python_name)
                if isinstance(liquid_inside_attr, list):
                    if source_container in liquid_inside_attr:
                        liquid_inside_attr.remove(source_container)
                        if self.verbose:
                            print(f"   ✅ Remove relation: {liquid_name} isInside {source_name}")
            
            # 2. Remove SourceContainer contains Liquid
            contains_prop = self.world.search_one(iri="*contains")
            if contains_prop and hasattr(source_container, contains_prop.python_name):
                source_contains_attr = getattr(source_container, contains_prop.python_name)
                if isinstance(source_contains_attr, list):
                    if liquid in source_contains_attr:
                        source_contains_attr.remove(liquid)
                        if self.verbose:
                            print(f"   ✅ Remove relation: {source_name} contains {liquid_name}")
            
            # Establish relations between target container and liquid
            # 3. Preferentially establish TargetContainer contains Liquid
            if contains_prop and hasattr(target_container, contains_prop.python_name):
                target_contains_attr = getattr(target_container, contains_prop.python_name)
                if isinstance(target_contains_attr, list):
                    if liquid not in target_contains_attr:
                        target_contains_attr.append(liquid)
                        if self.verbose:
                            print(f"   ✅ Establish relation: {target_name} contains {liquid_name}")
                else:
                    setattr(target_container, contains_prop.python_name, [liquid])
                    if self.verbose:
                        print(f"   ✅ Establish relation: {target_name} contains {liquid_name}")
            
            # 4. Establish Liquid isInside TargetContainer
            if is_inside_prop and hasattr(liquid, is_inside_prop.python_name):
                liquid_inside_attr = getattr(liquid, is_inside_prop.python_name)
                if isinstance(liquid_inside_attr, list):
                    if target_container not in liquid_inside_attr:
                        liquid_inside_attr.append(target_container)
                        if self.verbose:
                            print(f"   ✅ Establish relation: {liquid_name} isInside {target_name}")
                else:
                    setattr(liquid, is_inside_prop.python_name, [target_container])
                    if self.verbose:
                        print(f"   ✅ Establish relation: {liquid_name} isInside {target_name}")
            
            # 5. Process relation: SourceContainer isAbove TargetContainer (optional, for showing pouring process)
            is_above_prop = self.world.search_one(iri="*isAbove")
            if is_above_prop and hasattr(source_container, is_above_prop.python_name):
                source_above_attr = getattr(source_container, is_above_prop.python_name)
                if isinstance(source_above_attr, list):
                    if target_container not in source_above_attr:
                        source_above_attr.append(target_container)
                        if self.verbose:
                            print(f"   ✅ Establish pouring process relation: {source_name} isAbove {target_name}")
                else:
                    setattr(source_container, is_above_prop.python_name, [target_container])
                    if self.verbose:
                        print(f"   ✅ Establish pouring process relation: {source_name} isAbove {target_name}")
            
            if self.verbose:
                print(f"   ✅ pour action completed: {liquid_name} poured from {source_name} into {target_name}")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ pour action failed: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _handle_fill_liquid_action(self, parameters) -> bool:
        """
        Handle fillLiquid action - inject liquid into container
        
        Rules:
        - Established relations: Liquid isInside Container, Container contains Liquid
        - Possibly establish Tool isNear Container (if using tool)
        - Set container state: Container hasState FilledWithLiquidState
        """
        try:
            # Handle parameter format: support array format ['Kettle_1', 'coffee'] and dictionary format
            if isinstance(parameters, list):
                if len(parameters) >= 2:
                    container_name = parameters[0]
                    liquid_type = parameters[1]
                else:
                    print(f"   ❌ fillLiquid parameters insufficient: {parameters}")
                    return False
            else:
                container_name = parameters.get("object")  # Target container
                liquid_type = parameters.get("liquid")      # Liquid type
            
            if self.verbose:
                print(f"   🌊 Handle fillLiquid action: inject {liquid_type} into {container_name}")
            
            # Find container
            container = self.world.search_one(iri=f"*{container_name}")
            if not container:
                print(f"   ❌ Cannot find container: {container_name}")
                return False
            
            # Find liquid class and create instance (don't use generic search to avoid finding property instances)
            liquid_class = self.world.search_one(iri=f"*{liquid_type.capitalize()}")
            if not liquid_class:
                # Try other common liquid class name formats
                liquid_class = self.world.search_one(iri=f"*{liquid_type}")
                
            if liquid_class:
                # Verify this is a real liquid class (inherits from Liquid)
                liquid_base = self.world.search_one(iri="*Liquid")
                if liquid_base and hasattr(liquid_class, '__mro__') and liquid_base in liquid_class.__mro__:
                    liquid = liquid_class(f"{liquid_type}_instance_{len(list(self.world.individuals()))}")
                    
                    # Set liquid instance to located state (avoid LogicalInconsistency warning)
                    is_located_prop = self.world.search_one(iri="*isLocated")
                    if is_located_prop:
                        setattr(liquid, is_located_prop.python_name, True)
                        if self.verbose:
                            print(f"   ✅ Set {liquid_type} instance isLocated=True")
                else:
                    if self.verbose:
                        print(f"   ❌ Cannot find valid liquid type: {liquid_type}")
                    return False
            else:
                if self.verbose:
                    print(f"   ❌ Cannot find liquid type: {liquid_type}")
                return False
            
            # Establish containment relation between liquid and container - use OWL properties
            
            # 1. Preferentially establish Container contains Liquid
            contains_prop = self.world.search_one(iri="*contains")
            
            if contains_prop and hasattr(container, contains_prop.python_name):
                container_contains_attr = getattr(container, contains_prop.python_name)
                
                if isinstance(container_contains_attr, list):
                    if liquid not in container_contains_attr:
                        container_contains_attr.append(liquid)
                else:
                    setattr(container, contains_prop.python_name, [liquid])
            elif contains_prop:
                setattr(container, contains_prop.python_name, [liquid])
            
            # 2. Establish Liquid isInside Container
            is_inside_prop = self.world.search_one(iri="*isInside")
            
            if is_inside_prop and hasattr(liquid, is_inside_prop.python_name):
                liquid_inside_attr = getattr(liquid, is_inside_prop.python_name)
                if isinstance(liquid_inside_attr, list):
                    if container not in liquid_inside_attr:
                        liquid_inside_attr.append(container)
                else:
                    setattr(liquid, is_inside_prop.python_name, [container])
            elif is_inside_prop:
                setattr(liquid, is_inside_prop.python_name, [container])
            
            
            # Create FillLiquidAction instance (for safety rule triggering)
            fill_liquid_action_class = self.world.search_one(iri="*FillLiquidAction")
            if fill_liquid_action_class:
                import time
                action_instance_name = f"fill_liquid_action_{int(time.time() * 1000)}"
                fill_action_instance = fill_liquid_action_class(action_instance_name)
                
                # Establish FillLiquidAction hasTarget Container relation
                has_target_prop = self.world.search_one(iri="*hasTarget")
                if has_target_prop:
                    setattr(fill_action_instance, has_target_prop.python_name, [container])
                
                # Establish FillLiquidAction hasTarget Liquid relation  
                if has_target_prop and hasattr(fill_action_instance, has_target_prop.python_name):
                    current_targets = getattr(fill_action_instance, has_target_prop.python_name)
                    if isinstance(current_targets, list):
                        current_targets.append(liquid)
                    else:
                        setattr(fill_action_instance, has_target_prop.python_name, [container, liquid])
                
                if self.verbose:
                    print(f"   ✅ Created FillLiquidAction instance: {action_instance_name}")
                    print(f"   🎯 hasTarget: {container_name}, {liquid_type}")
            
            # Set container state to filled with liquid state
            filled_state = self.world.search_one(iri="*FilledWithLiquidState")
            has_state_prop = self.world.search_one(iri="*hasState")
            
            if filled_state and has_state_prop:
                try:
                    # Create filled state instance
                    filled_instance = filled_state(f"filled_state_{len(list(self.world.individuals()))}")
                    
                    # Remove empty state
                    if hasattr(container, has_state_prop.python_name):
                        current_states = getattr(container, has_state_prop.python_name)
                        if current_states:
                            # Remove EmptyState status
                            empty_states = [state for state in current_states if 'Empty' in str(type(state))]
                            for empty_state in empty_states:
                                current_states.remove(empty_state)
                    
                    # Set new filled state
                    if hasattr(container, has_state_prop.python_name):
                        getattr(container, has_state_prop.python_name).append(filled_instance)
                    else:
                        setattr(container, has_state_prop.python_name, [filled_instance])
                                            
                except Exception as e:
                    pass
            
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ fillLiquid action failed: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _handle_clean_action(self, parameters: Dict[str, str]) -> bool:
        """
        Handle clean action - clean items
        
        Rules:
        - Spatial relation impact: No direct impact
        - Description: Only changes item cleanliness state, does not affect spatial position
        """
        try:
            object_name = parameters.get("object")
            if not object_name:
                print(f"   ❌ clean action missing object parameter")
                return False
            
            if self.verbose:
                print(f"   🧹 Handle clean action: clean {object_name}")
            
            obj = self.world.search_one(iri=f"*{object_name}")
            if not obj:
                print(f"   ❌ Cannot find item to clean: {object_name}")
                return False
            
            # Find CleanState status class
            clean_state = self.world.search_one(iri="*CleanState")
            if clean_state:
                # Set clean status
                has_state_prop = self.world.search_one(iri="*hasState")
                if has_state_prop and hasattr(obj, has_state_prop.python_name):
                    # Create clean status instance
                    try:
                        clean_state_instance = clean_state(f"CleanState_for_{object_name}")
                        
                        # Set status
                        state_attr = getattr(obj, has_state_prop.python_name)
                        if isinstance(state_attr, list):
                            # Remove possible dirty status
                            dirty_states = [s for s in state_attr if 'Dirty' in str(s)]
                            for dirty_state in dirty_states:
                                state_attr.remove(dirty_state)
                            
                            # Add clean status
                            if clean_state_instance not in state_attr:
                                state_attr.append(clean_state_instance)
                        else:
                            setattr(obj, has_state_prop.python_name, [clean_state_instance])
                        
                        if self.verbose:
                            print(f"   ✅ Set clean status: {object_name} -> CleanState")
                    except Exception as e:
                        if self.verbose:
                            print(f"   ⚠️ Failed to create clean status instance: {e}")
                        # Backup plan: directly set status attribute
                        if hasattr(obj, 'isClean'):
                            setattr(obj, 'isClean', [True])
                        elif hasattr(obj, 'isDirty'):
                            setattr(obj, 'isDirty', [False])
                        if self.verbose:
                            print(f"   ✅ Use backup plan to set clean status: {object_name}")
            else:
                # If no CleanState, use direct attributes
                if hasattr(obj, 'isClean'):
                    setattr(obj, 'isClean', [True])
                    if self.verbose:
                        print(f"   ✅ Set isClean = True: {object_name}")
                elif hasattr(obj, 'isDirty'):
                    setattr(obj, 'isDirty', [False])
                    if self.verbose:
                        print(f"   ✅ Set isDirty = False: {object_name}")
                else:
                    if self.verbose:
                        print(f"   ⚠️ No cleanliness-related status or attributes found")
            
            if self.verbose:
                print(f"   ✅ clean action completed: {object_name} cleaned")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ clean action failed: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _handle_dirty_action(self, parameters: Dict[str, str]) -> bool:
        """
        Handle dirty action - make items dirty
        
        Rules:
        - Spatial relation impact: No direct impact
        - Description: Only changes item cleanliness state, does not affect spatial position
        """
        try:
            object_name = parameters.get("object")
            if not object_name:
                print(f"   ❌ dirty action missing object parameter")
                return False
            
            if self.verbose:
                print(f"   💫 Handle dirty action: make dirty {object_name}")
            
            obj = self.world.search_one(iri=f"*{object_name}")
            if not obj:
                print(f"   ❌ Cannot find item to make dirty: {object_name}")
                return False
            
            # Find DirtyState status class
            dirty_state = self.world.search_one(iri="*DirtyState")
            if dirty_state:
                # Set dirty status
                has_state_prop = self.world.search_one(iri="*hasState")
                if has_state_prop and hasattr(obj, has_state_prop.python_name):
                    # Create dirty status instance
                    try:
                        dirty_state_instance = dirty_state(f"DirtyState_for_{object_name}")
                        
                        # Set status
                        state_attr = getattr(obj, has_state_prop.python_name)
                        if isinstance(state_attr, list):
                            # Remove possible clean status
                            clean_states = [s for s in state_attr if 'Clean' in str(s)]
                            for clean_state in clean_states:
                                state_attr.remove(clean_state)
                            
                            # Add dirty status
                            if dirty_state_instance not in state_attr:
                                state_attr.append(dirty_state_instance)
                        else:
                            setattr(obj, has_state_prop.python_name, [dirty_state_instance])
                        
                        if self.verbose:
                            print(f"   ✅ Set dirty status: {object_name} -> DirtyState")
                    except Exception as e:
                        if self.verbose:
                            print(f"   ⚠️ Failed to create dirty status instance: {e}")
                        # Backup plan: directly set status attribute
                        if hasattr(obj, 'isDirty'):
                            setattr(obj, 'isDirty', [True])
                        elif hasattr(obj, 'isClean'):
                            setattr(obj, 'isClean', [False])
                        if self.verbose:
                            print(f"   ✅ Use backup plan to set dirty status: {object_name}")
            else:
                # If no DirtyState, use direct attributes
                if hasattr(obj, 'isDirty'):
                    setattr(obj, 'isDirty', [True])
                    if self.verbose:
                        print(f"   ✅ Set isDirty = True: {object_name}")
                elif hasattr(obj, 'isClean'):
                    setattr(obj, 'isClean', [False])
                    if self.verbose:
                        print(f"   ✅ Set isClean = False: {object_name}")
                else:
                    if self.verbose:
                        print(f"   ⚠️ No cleanliness-related status or attributes found")
            
            if self.verbose:
                print(f"   ✅ dirty action completed: {object_name} made dirty")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ dirty action failed: {e}")
                import traceback
                traceback.print_exc()
            return False

    def _handle_throw_action(self, parameters: Dict[str, str]) -> bool:
        """
        Handle throw action - throw out items
        
        Rules:
        - Remove relations: Agent isHolding Object, Object isConnectedTo Agent
        - Establish relations: Object may fly to some position or surface (specific position depends on parameters)
        - Update hand status: handIsEmpty = True
        """
        try:
            object_name = parameters.get("object")
            target_name = parameters.get("target", None)  # Optional target position
            
            if self.verbose:
                print(f"   🏀 Handle throw action: throw out {object_name}")
            
            # If no object specified, try to get robot-held items
            if not object_name:
                obj = self._get_robot_held_object()
                if not obj:
                    if self.verbose:
                        print(f"   ❌ Robot currently not holding any items to throw")
                    return False
                object_name = self._get_clean_name(obj)
            else:
                obj = self.world.search_one(iri=f"*{object_name}")
                if not obj:
                    if self.verbose:
                        print(f"   ❌ Cannot find item to throw: {object_name}")
                    return False
            
            # Clear robot's holding relation
            self._clear_robot_holding_after_put(obj)
            
            # If target position is specified, establish spatial relations
            if target_name:
                target = self.world.search_one(iri=f"*{target_name}")
                if target:
                    # Establish Object isOn Target relation (thrown onto surface)
                    is_on_prop = self.world.search_one(iri="*isOn")
                    if is_on_prop:
                        if hasattr(obj, is_on_prop.python_name):
                            on_attr = getattr(obj, is_on_prop.python_name)
                            if isinstance(on_attr, list):
                                on_attr.clear()
                                on_attr.append(target)
                            else:
                                setattr(obj, is_on_prop.python_name, [target])
                        else:
                            setattr(obj, is_on_prop.python_name, [target])
                        
                        if self.verbose:
                            print(f"   ✅ Establish relation: {object_name} isOn {target_name}")
                    
                    # Establish reverse relation Target supports Object
                    supports_prop = self.world.search_one(iri="*supports")
                    if supports_prop:
                        if hasattr(target, supports_prop.python_name):
                            supports_attr = getattr(target, supports_prop.python_name)
                            if isinstance(supports_attr, list):
                                if obj not in supports_attr:
                                    supports_attr.append(obj)
                            else:
                                setattr(target, supports_prop.python_name, [obj])
                        else:
                            setattr(target, supports_prop.python_name, [obj])
                        
                        if self.verbose:
                            print(f"   ✅ Establish relation: {target_name} supports {object_name}")
                else:
                    if self.verbose:
                        print(f"   ⚠️ Cannot find target position: {target_name}")
            
            if self.verbose:
                print(f"   ✅ throw action completed: {object_name} thrown out")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ throw action failed: {e}")
                import traceback
                traceback.print_exc()
            return False

    def _handle_drop_action(self, parameters: Dict[str, str]) -> bool:
        """
        Handle drop action - drop items
        
        Rules:
        - Remove relations: Agent isHolding Object, Object isConnectedTo Agent
        - Establish relations: Object may be placed at some position or surface (specific position depends on parameters)
        - Update hand status: handIsEmpty = True
        """
        try:
            object_name = parameters.get("object")
            target_name = parameters.get("target", None)  # Optional target position
            
            if self.verbose:
                print(f"   📦 Handle drop action: drop {object_name}")
            
            # If no object specified, try to get robot-held items
            if not object_name:
                obj = self._get_robot_held_object()
                if not obj:
                    if self.verbose:
                        print(f"   ❌ Robot currently not holding any items to drop")
                    return False
                object_name = self._get_clean_name(obj)
            else:
                obj = self.world.search_one(iri=f"*{object_name}")
                if not obj:
                    if self.verbose:
                        print(f"   ❌ Cannot find item to drop: {object_name}")
                    return False
            
            # Clear robot's holding relation
            self._clear_robot_holding_after_put(obj)
            
            # If target position is specified, establish spatial relations
            if target_name:
                target = self.world.search_one(iri=f"*{target_name}")
                if target:
                    # Establish Object isOn Target relation (placed on surface)
                    is_on_prop = self.world.search_one(iri="*isOn")
                    if is_on_prop:
                        if hasattr(obj, is_on_prop.python_name):
                            on_attr = getattr(obj, is_on_prop.python_name)
                            if isinstance(on_attr, list):
                                on_attr.clear()
                                on_attr.append(target)
                            else:
                                setattr(obj, is_on_prop.python_name, [target])
                        else:
                            setattr(obj, is_on_prop.python_name, [target])
                        
                        if self.verbose:
                            print(f"   ✅ Establish relation: {object_name} isOn {target_name}")
                    
                    # Establish reverse relation Target supports Object
                    supports_prop = self.world.search_one(iri="*supports")
                    if supports_prop:
                        if hasattr(target, supports_prop.python_name):
                            supports_attr = getattr(target, supports_prop.python_name)
                            if isinstance(supports_attr, list):
                                if obj not in supports_attr:
                                    supports_attr.append(obj)
                            else:
                                setattr(target, supports_prop.python_name, [obj])
                        else:
                            setattr(target, supports_prop.python_name, [obj])
                        
                        if self.verbose:
                            print(f"   ✅ Establish relation: {target_name} supports {object_name}")
                else:
                    if self.verbose:
                        print(f"   ⚠️ Cannot find target position: {target_name}")
            
            if self.verbose:
                print(f"   ✅ drop action completed: {object_name} dropped")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ drop action failed: {e}")
                import traceback
                traceback.print_exc()
            return False

    def _handle_break_action(self, parameters: Dict[str, str]) -> bool:
        """
        Handle break action - break items
        
        Rules:
        - Change item state to BrokenState
        - May produce broken fragments or change item properties
        """
        try:
            object_name = parameters.get("object")
            
            if self.verbose:
                print(f"   🔨 Handle break action: break {object_name}")
            
            if not object_name:
                if self.verbose:
                    print(f"   ❌ break action missing object parameter")
                return False
            
            obj = self.world.search_one(iri=f"*{object_name}")
            if not obj:
                if self.verbose:
                    print(f"   ❌ Cannot find item to break: {object_name}")
                return False
            
            # Set broken state
            broken_state = self.world.search_one(iri="*BrokenState")
            has_state_prop = self.world.search_one(iri="*hasState")
            
            if broken_state and has_state_prop:
                try:
                    # Create broken state instance
                    broken_instance = broken_state(f"broken_state_{len(list(self.world.individuals()))}")
                    
                    # Set item's broken state
                    if hasattr(obj, has_state_prop.python_name):
                        state_attr = getattr(obj, has_state_prop.python_name)
                        if isinstance(state_attr, list):
                            state_attr.clear()
                            state_attr.append(broken_instance)
                        else:
                            setattr(obj, has_state_prop.python_name, [broken_instance])
                    else:
                        setattr(obj, has_state_prop.python_name, [broken_instance])
                    
                    if self.verbose:
                        print(f"   ✅ Set broken state: {object_name} -> BrokenState")
                        
                except Exception as e:
                    if self.verbose:
                        print(f"   ⚠️ Failed to set broken state: {e}")
            else:
                if self.verbose:
                    print(f"   ⚠️ Cannot find BrokenState or hasState property")
            
            if self.verbose:
                print(f"   ✅ break action completed: {object_name} broken")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ break action failed: {e}")
                import traceback
                traceback.print_exc()
            return False

    def _handle_slice_action(self, parameters: Dict[str, str]) -> bool:
        """
        Handle slice action - slice items
        
        Rules:
        - Create SliceAction instance
        - Establish SliceAction hasAgent relation
        - Change item state to SlicedState
        """
        try:
            object_name = parameters.get("object")
            agent_name = parameters.get("agent", "my_robot")
            
            if self.verbose:
                print(f"   🔪 Handle slice action: slice {object_name}")
            
            if not object_name:
                if self.verbose:
                    print(f"   ❌ slice action missing object parameter")
                return False
            
            obj = self.world.search_one(iri=f"*{object_name}")
            if not obj:
                if self.verbose:
                    print(f"   ❌ Cannot find object: {object_name}")
                return False
                
            # 1. Create SliceAction instance
            slice_action_class = self.world.search_one(iri="*SliceAction")
            if slice_action_class:
                import time
                action_instance_name = f"slice_action_{int(time.time() * 1000)}"
                slice_action_instance = slice_action_class(action_instance_name)
                
                if self.verbose:
                    print(f"   ✅ Created SliceAction instance: {action_instance_name}")
                
                # 2. Establish hasActor relation
                agent = self.world.search_one(iri=f"*{agent_name}")
                has_actor_prop = self.world.search_one(iri="*hasActor")
                if agent and has_actor_prop:
                    setattr(slice_action_instance, has_actor_prop.python_name, [agent])
                    if self.verbose:
                        print(f"   ✅ Establish relation: {action_instance_name} hasActor {agent_name}")
                
                # 3. Establish hasTarget relation
                has_target_prop = self.world.search_one(iri="*hasTarget")
                if has_target_prop:
                    setattr(slice_action_instance, has_target_prop.python_name, [obj])
                    if self.verbose:
                        print(f"   ✅ Establish relation: {action_instance_name} hasTarget {object_name}")
            
            # Set sliced state
            sliced_state = self.world.search_one(iri="*SlicedState")
            has_state_prop = self.world.search_one(iri="*hasState")
            
            if sliced_state and has_state_prop:
                try:
                    # Create sliced state instance
                    sliced_instance = sliced_state(f"sliced_state_{len(list(self.world.individuals()))}")
                    
                    # Set item's sliced state
                    if hasattr(obj, has_state_prop.python_name):
                        state_attr = getattr(obj, has_state_prop.python_name)
                        if isinstance(state_attr, list):
                            state_attr.clear()
                            state_attr.append(sliced_instance)
                        else:
                            setattr(obj, has_state_prop.python_name, [sliced_instance])
                    else:
                        setattr(obj, has_state_prop.python_name, [sliced_instance])
                    
                    if self.verbose:
                        print(f"   ✅ Set sliced state: {object_name} -> SlicedState")
                        
                except Exception as e:
                    if self.verbose:
                        print(f"   ⚠️ Failed to set sliced state: {e}")
            else:
                if self.verbose:
                    print(f"   ⚠️ Cannot find SlicedState or hasState property")
            
            if self.verbose:
                print(f"   ✅ slice action completed: {object_name} sliced")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ slice action failed: {e}")
                import traceback
                traceback.print_exc()
            return False

    def _handle_cook_action(self, parameters: Dict[str, str]) -> bool:
        """
        Handle cook action - only create CookAction instance, do not modify world state
        
        According to user requirements, this action is only used to trigger LogicalInconsistencyConcept danger detection,
        to remind users they should use specific cooking tools rather than abstract cook action.
        """
        try:
            object_name = parameters.get("object", "unknown_object")
            
            # Create CookAction instance
            CookAction = self.world.search_one(iri="*CookAction")
            if CookAction:
                # Generate unique instance name
                import time
                instance_name = f"cook_action_{int(time.time() * 1000)}"
                cook_instance = CookAction(instance_name)
                
                if self.verbose:
                    print(f"   🍳 cook action: Create CookAction instance {instance_name} (target: {object_name})")
                    print(f"   ⚠️ Note: Direct cook action will trigger LogicalInconsistency warning")
            else:
                if self.verbose:
                    print(f"   ⚠️ Cannot find CookAction class, using default handling")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ cook action failed: {e}")
                import traceback
                traceback.print_exc()
            return False