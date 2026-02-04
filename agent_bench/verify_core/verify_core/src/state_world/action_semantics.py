"""
Action semantics definition module
Defines preconditions and effects for each action
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import owlready2 as owl


@dataclass
class ActionEffect:
    """Action effect: assertions to add or remove"""
    add_assertions: List[Tuple[str, str, Any]]  # (subject, property, object)
    remove_assertions: List[Tuple[str, str, Any]]  # (subject, property, object)


@dataclass
class ActionDefinition:
    """Action definition: contains preconditions and effects"""
    name: str
    parameters: List[str]
    preconditions: List[Tuple[str, str, Any]]  # (subject, property, object)
    effects: ActionEffect
    description: str


class ActionSemantics:
    """Action semantics manager"""
    
    def __init__(self):
        self.actions = self._define_actions()
    
    def _define_actions(self) -> Dict[str, ActionDefinition]:
        """Define all supported actions and their semantics"""
        
        actions = {}
        
        # =============== PICK ACTION ===============
        actions['pick'] = ActionDefinition(
            name='pick',
            parameters=['agent', 'object'],
            preconditions=[
                ('agent', 'handIsEmpty', True),  # Agent's hand is empty
                ('object', 'isAt', 'some_location'),  # Object is at some location (wildcard)
            ],
            effects=ActionEffect(
                add_assertions=[
                    ('agent', 'isHolding', 'object'),  # Agent holds object
                    ('agent', 'handIsEmpty', False),   # Hand is no longer empty
                ],
                remove_assertions=[
                    ('object', 'isAt', 'previous_location'),  # Object is no longer at previous location
                ]
            ),
            description='Agent picks up object'
        )
        
        # =============== PUT ACTION ===============
        actions['put'] = ActionDefinition(
            name='put',
            parameters=['agent', 'object', 'surface'],
            preconditions=[
                ('agent', 'isHolding', 'object'),  # Agent is holding object
            ],
            effects=ActionEffect(
                add_assertions=[
                    ('agent', 'handIsEmpty', True),    # Hand becomes empty
                    ('object', 'isAt', 'surface'),     # Object is located on surface
                    ('surface', 'contains', 'object'), # Surface contains object (if it's a container)
                ],
                remove_assertions=[
                    ('agent', 'isHolding', 'object'),  # No longer holding object
                ]
            ),
            description='Agent places object on surface'
        )
        
        # =============== OPEN ACTION ===============
        actions['open'] = ActionDefinition(
            name='open',
            parameters=['agent', 'object'],
            preconditions=[
                ('object', 'doorIsClosed', True),  # Door is closed
            ],
            effects=ActionEffect(
                add_assertions=[
                    ('object', 'doorIsOpen', True),   # Door becomes open
                ],
                remove_assertions=[
                    ('object', 'doorIsClosed', True), # Door is no longer closed
                ]
            ),
            description='Agent opens object door'
        )
        
        # =============== CLOSE ACTION ===============
        actions['close'] = ActionDefinition(
            name='close',
            parameters=['agent', 'object'],
            preconditions=[
                ('object', 'doorIsOpen', True),  # Door is open
            ],
            effects=ActionEffect(
                add_assertions=[
                    ('object', 'doorIsClosed', True), # Door becomes closed
                ],
                remove_assertions=[
                    ('object', 'doorIsOpen', True),   # Door is no longer open
                ]
            ),
            description='Agent closes object door'
        )
        
        # =============== TURN ON ACTION ===============
        actions['turn_on'] = ActionDefinition(
            name='turn_on',
            parameters=['agent', 'object'],
            preconditions=[
                ('object', 'isOperational', True),  # Device is operational
            ],
            effects=ActionEffect(
                add_assertions=[
                    ('object', 'hasState', 'OnState'),      # Device state is on
                    ('object', 'isOperating', 'OnState'),   # Device is operating
                ],
                remove_assertions=[
                    ('object', 'hasState', 'OffState'),     # Device is no longer in off state
                ]
            ),
            description='Agent turns on electrical device'
        )
        
        # =============== TURN OFF ACTION ===============
        actions['turn_off'] = ActionDefinition(
            name='turn_off',
            parameters=['agent', 'object'],
            preconditions=[
                ('object', 'hasState', 'OnState'),  # Device is on
            ],
            effects=ActionEffect(
                add_assertions=[
                    ('object', 'hasState', 'OffState'),     # Device state is off
                ],
                remove_assertions=[
                    ('object', 'hasState', 'OnState'),      # Device is no longer in on state
                    ('object', 'isOperating', 'OnState'),   # Device is no longer operating
                ]
            ),
            description='Agent turns off electrical device'
        )
        
        # =============== FIND ACTION ===============
        actions['find'] = ActionDefinition(
            name='find',
            parameters=['agent', 'object'],
            preconditions=[
                # Find action usually has no strict preconditions
            ],
            effects=ActionEffect(
                add_assertions=[
                    ('agent', 'isLocatedAt', 'object'),  # Agent moves to object location
                ],
                remove_assertions=[
                    # Find action usually doesn't remove any assertions
                ]
            ),
            description='Agent searches for and moves to object location'
        )
        
        # =============== THROW ACTION ===============
        actions['throw'] = ActionDefinition(
            name='throw',
            parameters=['agent', 'object'],
            preconditions=[
                ('agent', 'isHolding', 'object'),  # Agent is holding object
            ],
            effects=ActionEffect(
                add_assertions=[
                    # throw action will create ThrowAction instance, triggering safety rules
                ],
                remove_assertions=[
                    ('agent', 'isHolding', 'object'),      # Agent no longer holds object
                    ('agent', 'handIsEmpty', False),       # Hand empty state changes
                ]
            ),
            description='Agent throws object'
        )
        
        # =============== FILL LIQUID ACTION ===============
        actions['fillLiquid'] = ActionDefinition(
            name='fillLiquid',
            parameters=['agent', 'object', 'liquid'],
            preconditions=[
                ('object', 'hasState', 'EmptyState'),  # Container is empty
            ],
            effects=ActionEffect(
                add_assertions=[
                    ('object', 'hasState', 'FilledWithLiquidState'),  # Container becomes filled with liquid state
                    ('liquid', 'isInside', 'object'),                 # Liquid is inside container
                    ('object', 'contains', 'liquid'),                 # Container contains liquid
                ],
                remove_assertions=[
                    ('object', 'hasState', 'EmptyState'),             # Container is no longer empty
                ]
            ),
            description='Agent fills container with liquid'
        )
        
        return actions
    
    def get_action(self, action_name: str) -> ActionDefinition:
        """Get action definition"""
        if action_name not in self.actions:
            raise ValueError(f"Unknown action: {action_name}")
        return self.actions[action_name]
    
    def validate_preconditions(self, action_name: str, world: owl.World, 
                             parameters: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate if action preconditions are satisfied"""
        action = self.get_action(action_name)
        errors = []
        
        for subj_param, prop, obj_value in action.preconditions:
            # Parse parameters
            if subj_param in parameters:
                subject = world.search_one(iri=f"*{parameters[subj_param]}")
                if not subject:
                    errors.append(f"Cannot find entity: {parameters[subj_param]}")
                    continue
                
                # Check property value
                if hasattr(subject, prop):
                    current_value = getattr(subject, prop)
                    if obj_value != 'some_location' and current_value != obj_value:
                        errors.append(f"{parameters[subj_param]}.{prop} = {current_value}, expected: {obj_value}")
                else:
                    errors.append(f"{parameters[subj_param]} has no property {prop}")
        
        return len(errors) == 0, errors
    
    def apply_effects(self, action_name: str, world: owl.World, 
                     parameters: Dict[str, str], current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply action effects, modify world state"""
        action = self.get_action(action_name)
        new_state = current_state.copy()
        
        # Apply added assertions
        for subj_param, prop, obj_param in action.effects.add_assertions:
            if subj_param in parameters:
                subject_name = parameters[subj_param]
                
                # Parse object value
                if obj_param in parameters:
                    obj_value = parameters[obj_param]
                elif obj_param in ['OnState', 'OffState']:
                    obj_value = obj_param
                elif isinstance(obj_param, bool):
                    obj_value = obj_param
                else:
                    obj_value = obj_param
                
                # Update state
                if subject_name not in new_state:
                    new_state[subject_name] = {}
                new_state[subject_name][prop] = obj_value
        
        # Apply removed assertions
        for subj_param, prop, obj_param in action.effects.remove_assertions:
            if subj_param in parameters:
                subject_name = parameters[subj_param]
                if subject_name in new_state and prop in new_state[subject_name]:
                    if obj_param == 'previous_location':
                        # Special handling: remove location information
                        if 'isAt' in new_state[subject_name]:
                            del new_state[subject_name]['isAt']
                    else:
                        del new_state[subject_name][prop]
        
        return new_state


def parse_action_sequence(action_sequence: List[str]) -> List[Tuple[str, Dict[str, str]]]:
    """Parse action sequence strings into structured format"""
    parsed_actions = []
    
    for action_str in action_sequence:
        parts = action_str.strip().split()
        if len(parts) < 1:
            continue
            
        action_name = parts[0].lower().replace(' ', '_')
        
        # Debug action parsing
        if parts[0].lower() in ['fillliquid', 'fill_liquid']:
            print(f"   🔍 [Action Parsing] Original: {parts[0]}, Converted: {action_name}, Parameters: {parts[1:]}")
        
        # Parse parameters based on action type
        if action_name == 'find':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name == 'pick':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name in ['put', 'place']:
            if len(parts) >= 4:  # put A in/on B
                obj_name = parts[1]
                preposition = parts[2].lower()  # in or on
                surface_name = parts[3]
                
                parsed_actions.append(('put', {
                    'agent': 'my_robot',
                    'object': obj_name,
                    'surface': surface_name,
                    'preposition': preposition
                }))
            elif len(parts) >= 3 and parts[1].lower() in ['in', 'on']:
                # put in B or put on B, use currently held object
                preposition = parts[1].lower()
                surface_name = parts[2]
                parsed_actions.append(('put', {
                    'agent': 'my_robot',
                    'object': None,  # Indicates automatic retrieval needed
                    'surface': surface_name,
                    'preposition': preposition
                }))
            elif len(parts) >= 2:
                # put B, default to put on B, use currently held object
                surface_name = parts[1]
                parsed_actions.append(('put', {
                    'agent': 'my_robot',
                    'object': None,  # Indicates automatic retrieval needed
                    'surface': surface_name,
                    'preposition': 'on'  # Default to on
                }))
        elif action_name == 'open':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name == 'close':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name in ['turn', 'switch'] and len(parts) >= 3:
            if parts[1].lower() == 'on':
                parsed_actions.append(('turn_on', {
                    'agent': 'my_robot',
                    'object': parts[2]
                }))
            elif parts[1].lower() == 'off':
                parsed_actions.append(('turn_off', {
                    'agent': 'my_robot',
                    'object': parts[2]
                }))
        elif action_name == 'pour':
            if len(parts) >= 6 and parts[2].lower() == 'from' and parts[4].lower() == 'to':
                # pour TestWater_Action from TestKettle_Action to TestCup_Action
                parsed_actions.append((action_name, {
                    'agent': 'my_robot',
                    'object': parts[1],      # liquid
                    'source': parts[3],      # source container
                    'target': parts[5]       # target container
                }))
            elif len(parts) >= 3:
                # pour SourceContainer TargetContainer
                parsed_actions.append((action_name, {
                    'agent': 'my_robot',
                    'source': parts[1],      # source container
                    'target': parts[2]       # target container
                }))
            elif len(parts) == 1:
                # pour - infer source container (currently held) and target (last found object) from context
                parsed_actions.append((action_name, {
                    'agent': 'my_robot',
                    'source': 'current_held_object',  # currently held object
                    'target': 'last_found_object'     # last found object
                }))
        elif action_name == 'clean':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name == 'dirty':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name == 'throw':
            if len(parts) > 1:
                # throw with specified object
                parsed_actions.append((action_name, {
                    'agent': 'my_robot',
                    'object': parts[1]
                }))
            else:
                # throw without specifying object (throw currently held object)
                parsed_actions.append((action_name, {
                    'agent': 'my_robot',
                    'object': None  # will get currently held object in executor
                }))
        elif action_name == 'drop':
            # drop action supports two forms:
            # 1. "drop" - drop currently held object (no need to specify object)
            # 2. "drop ObjectName" - drop specified object
            if len(parts) > 1:
                # drop with specified object
                parsed_actions.append((action_name, {
                    'agent': 'my_robot',
                    'object': parts[1]
                }))
            else:
                # drop without specifying object (drop currently held object)
                parsed_actions.append((action_name, {
                    'agent': 'my_robot',
                    'object': 'current_held_object'  # use placeholder, will be replaced with actual held object later
                }))
        elif action_name == 'break':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name == 'slice':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name == 'cook':
            parsed_actions.append((action_name, {
                'agent': 'my_robot',
                'object': parts[1]
            }))
        elif action_name in ['fillliquid', 'fill_liquid'] and len(parts) >= 3:
            # fillLiquid TestCup_1 coffee
            parsed_actions.append(('fillLiquid', {
                'agent': 'my_robot',
                'object': parts[1],      # target container
                'liquid': parts[2]       # liquid type
            }))
    
    return parsed_actions
