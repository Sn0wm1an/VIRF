"""
World state manager
Responsible for capturing, cloning, verifying, and detailed printing of world states
"""

from typing import Dict, Any
from datetime import datetime
import owlready2 as owl


class WorldStateManager:
    """World state manager"""
    
    def __init__(self, world: owl.World, verbose: bool = False):
        """
        Initialize world state manager
        
        Args:
            world: OWL world instance
            verbose: Whether to enable verbose logging
        """
        self.world = world
        self.verbose = verbose
    
    def _determine_property_type(self, property_name: str, property_value) -> str:
        """
        Determine the correct type of the property value, especially spatial relationships
        
        Args:
            property_name: Property name
            property_value: Property value
            
        Returns:
            Property type string
        """
        # 🔑 Spatial relationship property list
        spatial_properties = [
            'contains', 'isInside', 'isOn', 'isAbove', 'touches', 
            'isNear', 'isAt', 'isConnectedTo', 'supports', 'isAdjacentTo'
        ]
        
        # State-related properties
        state_properties = ['hasState', 'isOperating']
        
        # Material-related properties  
        material_properties = ['hasMaterial']
        
        if property_name in spatial_properties:
            if self.verbose:
                print(f"   🗺️ Identified spatial relationship: {property_name} -> spatial")
            return 'spatial'
        elif property_name in state_properties:
            return 'state'
        elif property_name in material_properties:
            return 'material'
        elif 'State' in str(type(property_value)):
            return 'state'
        else:
            return 'instance'

    def _get_clean_class_name(self, obj) -> str:
        """
        Get the cleaned class name, avoiding FusionClass leakage
        
        Args:
            obj: OWL object instance
            
        Returns:
            Cleaned original class name
        """
        try:
            # Get object type
            obj_type = type(obj)
            type_str = str(obj_type)
            
            if self.verbose:
                print(f"   🔍 Original type string: {type_str}")
            
            # Check if it's a FusionClass
            if 'FusionClass' in type_str:
                if self.verbose:
                    print(f"   ⚠️ Detected FusionClass, trying to extract original class name")
                
                # Try to extract the original class name from the object's is_a relationship
                if hasattr(obj, 'is_a') and obj.is_a:
                    for cls in obj.is_a:
                        if hasattr(cls, '__name__'):
                            class_name = cls.__name__
                            # Prioritize selecting a class that is not Thing and does not contain FusionClass
                            if class_name != 'Thing' and 'FusionClass' not in class_name:
                                if self.verbose:
                                    print(f"   ✅ Extracted class name from is_a relationship: {class_name}")
                                return class_name
                
                # If is_a method fails, try to get from __bases__
                for base in obj_type.__bases__:
                    if hasattr(base, '__name__'):
                        base_name = base.__name__
                        if not base_name.startswith('FusionClass') and base_name != 'Thing':
                            if self.verbose:
                                print(f"   ✅ Get class name from __bases__: {base_name}")
                            return base_name
                
                # Finally try to parse FusionClass string
                # <FusionClass object.Object, object.Pot> -> take the last specific class name
                if ',' in type_str:
                    parts = type_str.split(',')
                    for part in reversed(parts):  # Search from back to front for more specific class
                        part = part.strip()
                        if '.' in part:
                            class_name = part.split('.')[-1].replace('>', '').strip()
                            if class_name and class_name != 'Object':
                                if self.verbose:
                                    print(f"   ✅ Get class name from FusionClass parsing: {class_name}")
                                return class_name
            
            # Regular processing for non-FusionClass
            if '.' in type_str:
                class_name = type_str.split('.')[-1]
            else:
                class_name = type_str
            
            # Clean various possible ending symbols
            class_name = class_name.replace("'>", "").replace("'", "").replace(">", "").strip()
            
            if self.verbose:
                print(f"   ✅ Cleaned class name: {class_name}")
            
            return class_name
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Class name cleaning failed: {e}, using fallback method")
            # Fallback method: extract directly from string
            type_str = str(type(obj))
            return type_str.split('.')[-1].replace("'>", "").replace("'", "").replace(">", "").strip()
    
    def capture_world_state(self) -> Dict[str, Any]:
        """Capture detailed information about the current world state"""
        try:
            individuals = list(self.world.individuals())
            classes = list(self.world.classes())
            properties = list(self.world.properties())
            
            # Add debug information
            if self.verbose:
                print(f"🔍 Debug information:")
                print(f"   - individuals count: {len(individuals)}")
                print(f"   - classes count: {len(classes)}")
                print(f"   - properties count: {len(properties)}")
                if individuals:
                    print(f"   - First 3 individuals: {[str(ind) for ind in individuals[:3]]}")
                    print(f"   - First 3 individuals' name: {[getattr(ind, 'name', 'NO_NAME') for ind in individuals[:3]]}")
                    print(f"   - First 3 individuals' type: {[str(type(ind)) for ind in individuals[:3]]}")
            
            # Capture instance and its properties
            individuals_detail = {}
            processed_count = 0
            for ind in individuals:
                # Debug each individual processing
                if self.verbose:
                    print(f"   🔄 Processing individual: {ind} (name: {getattr(ind, 'name', 'NO_NAME')}, type: {type(ind)})")
                
                # Check name validity
                ind_name = getattr(ind, 'name', None)
                if not ind_name:
                    if self.verbose:
                        print(f"   ⚠️ Skip individual with no name: {ind}")
                    continue
                # Use cleaned class name to avoid FusionClass leakage
                clean_class_name = self._get_clean_class_name(ind)
                
                ind_info = {
                    'class': clean_class_name,
                    'namespace': str(ind.namespace),
                    'properties': {}
                }
                
                # Capture all property values of the instance
                for prop in properties:
                    if hasattr(ind, prop.python_name):
                        prop_value = getattr(ind, prop.python_name)
                        
                        
                        if prop_value:
                            if isinstance(prop_value, list):
                                processed_values = []
                                for v in prop_value:
                                    if isinstance(v, owl.Thing):
                                        # Key fix: correctly identify spatial relationship type
                                        value_type = self._determine_property_type(prop.python_name, v)
                                        processed_values.append({'value': v.name, 'type': value_type})
                                    elif isinstance(v, (bool, int, float, str)):
                                        processed_values.append({'value': v, 'type': 'literal'})
                                    elif isinstance(v, owl.entity.ThingClass):
                                        # Skip classes that might have been added to properties by the reasoner
                                        continue
                                    else:
                                        if self.verbose:
                                            print(f"   ⚠️ Found unknown type property value: {v} (type: {type(v)}), serialized as 'unknown'.")
                                        processed_values.append({'value': str(v), 'type': 'unknown'})
                                if processed_values:
                                    ind_info['properties'][prop.python_name] = processed_values
                            else:
                                if isinstance(prop_value, owl.Thing):
                                    # Key fix: correctly identify spatial relationship type
                                    value_type = self._determine_property_type(prop.python_name, prop_value)
                                    ind_info['properties'][prop.python_name] = {'value': prop_value.name, 'type': value_type}
                                elif isinstance(prop_value, (bool, int, float, str)):
                                    ind_info['properties'][prop.python_name] = {'value': prop_value, 'type': 'literal'}
                                elif isinstance(prop_value, owl.entity.ThingClass):
                                    # Skip classes that might have been added to properties by the reasoner
                                    pass
                                else:
                                    if self.verbose:
                                        print(f"   ⚠️ Found unknown type property value: {prop_value} (type: {type(prop_value)}), serialized as 'unknown'.")
                                    ind_info['properties'][prop.python_name] = {'value': str(prop_value), 'type': 'unknown'}
                
                # Add to dictionary (using validated name)
                individuals_detail[ind_name] = ind_info
                processed_count += 1
                
                if self.verbose:
                    print(f"   ✅ Processed individual: {ind_name}")
            
            # Final debug information
            if self.verbose:
                print(f"🔍 Final statistics:")
                print(f"   - Original individuals count: {len(individuals)}")
                print(f"   - Actual processed count: {processed_count}")
                print(f"   - individuals_detail size: {len(individuals_detail)}")
                print(f"   - individuals_detail keys: {list(individuals_detail.keys())}")
            
            state = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'individuals_count': len(individuals),
                    'classes_count': len(classes),
                    'properties_count': len(properties)
                },
                'individuals': individuals_detail,
                'classes': [str(cls) for cls in classes],
                'properties': [str(prop) for prop in properties]
            }
            
            return state
            
        except Exception as e:
            print(f"Failed to capture world state: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'summary': {'individuals_count': 0, 'classes_count': 0, 'properties_count': 0}
            }
    
    def clone_world_state(self):
        """Create a deep copy of the world state (for multi-threading preparation)"""
        try:
            if self.verbose:
                print("📋 Creating world state snapshot...")
            
            # Capture current state
            current_state = self.capture_world_state()
            
            # TODO: Implement true world cloning (need to copy the entire world object)
            # Currently return state snapshot, can be used for state comparison and verification later
            
            clone_info = {
                'clone_timestamp': datetime.now().isoformat(),
                'original_state': current_state,
                'clone_id': f"clone_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            }
            
            if self.verbose:
                print(f"✅ World state snapshot created: {clone_info['clone_id']}")
            return clone_info
            
        except Exception as e:
            print(f"❌ Failed to create world state snapshot: {e}")
            return None

    def reconstruct_world_from_snapshot(self, world_snapshot: Dict[str, Any]) -> Any:
        """Reconstruct world state from snapshot"""
        import owlready2 as owl
        from ..ontology_loader import OntologyLoader
        from ..abox_tbox_mapper import ABoxTBoxMapper

        try:
            # 1. Create a new World instance
            temp_world = owl.World()

            # 2. Load all ontologies
            loader = OntologyLoader(verbose=self.verbose)
            temp_world, main_onto = loader.load_all_ontologies(world_instance=temp_world)

            # 3. Use ABoxTBoxMapper to reconstruct state
            mapper = ABoxTBoxMapper(temp_world, main_onto, verbose=self.verbose)
            
            # 4. Convert data from snapshot
            instances_to_create = []
            assertions_to_create = []

            individuals_data = world_snapshot.get('individuals', {})
            for inst_name, inst_details in individuals_data.items():
                class_name_full = inst_details.get('class', '')
                class_name = class_name_full.split('.')[-1].replace("'>", "").replace("'", "")
                
                if class_name:
                    instances_to_create.append({
                        "class_name": class_name,
                        "instance_name": inst_name
                    })


                for prop_name, prop_value_data in inst_details.get('properties', {}).items():
                    values_list = prop_value_data if isinstance(prop_value_data, list) else [prop_value_data]
                    
                    for value_item in values_list:
                        if isinstance(value_item, dict) and 'value' in value_item and 'type' in value_item:
                            object_value = value_item['value']
                            object_type = value_item['type']
                            
                            
                            assertions_to_create.append({
                                "subject": inst_name,
                                "property": prop_name,
                                "object": {'value': object_value, 'type': object_type},
                                "type": object_type
                            })
                        else:
                            # Fallback for any unexpected old format or malformed data
                            object_value = value_item
                            object_type = 'unknown'
                            if isinstance(object_value, bool):
                                object_type = 'literal'
                            elif isinstance(object_value, str) and 'State' in object_value:
                                object_type = 'state'
                            elif isinstance(object_value, str):
                                object_type = 'instance'
                            
                            assertions_to_create.append({
                                "subject": inst_name,
                                "property": prop_name,
                                "object": {'value': object_value, 'type': object_type},
                                "type": object_type
                            })

            json_data = {
                'instances': instances_to_create,
                'assertions': assertions_to_create
            }
            
            # 5. Execute mapping
            mapping_result = mapper.process_json_mapping(json_data)
            
            if not mapping_result['success']:
                print(f"   ⚠️  State reconstruction failed: {mapping_result['errors']}")
                return None

            return temp_world, main_onto

        except Exception as e:
            print(f"   ❌ State reconstruction failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def validate_world_state(self, step_number: int, action: str) -> Dict[str, Any]:
        """Validate world state correctness"""
        try:
            if self.verbose:
                print(f"✅ Step {step_number} world state validation...")
            
            validation_result = {
                'step_number': step_number,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'validation_passed': True,
                'issues': [],
                'world_state': self.capture_world_state()
            }
            
            # Basic consistency check
            individuals = list(self.world.individuals())
            
            # Check for my_robot
            my_robot = self.world.search_one(iri="*my_robot")
            if not my_robot:
                validation_result['issues'].append("Missing default robot my_robot")
                validation_result['validation_passed'] = False
            else:
                if self.verbose:
                    print(f"   ✅ Default robot exists: {my_robot}")
                
                # Check robot properties
                if hasattr(my_robot, 'isHolding'):
                    holding = getattr(my_robot, 'isHolding')
                    if self.verbose:
                        if holding:
                            print(f"   📦 Robot is holding: {[str(item) for item in holding]}")
                        else:
                            print(f"   🆓 Robot is not holding anything")
            
            # Check instance count
            if len(individuals) == 0:
                validation_result['issues'].append("World has no instances")
                validation_result['validation_passed'] = False
            
            # Print validation result
            if self.verbose:
                if validation_result['validation_passed']:
                    print(f"   ✅ World state validation passed")
                else:
                    print(f"   ⚠️ World state validation failed: {validation_result['issues']}")
            
            return validation_result
            
        except Exception as e:
            print(f"❌ World state validation failed: {e}")
            return {
                'step_number': step_number,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'validation_passed': False,
                'issues': [f"World state validation failed: {str(e)}"],
                'world_state': {}
            }
    
    def print_detailed_world_state(self, step_number: int, action: str):
        """Print detailed world state information for testing and debugging"""
        print(f"\n{'='*60}")
        print(f"🌍 Step {step_number} world state - Action: {action}")
        print(f"{'='*60}")
        
        try:
            # Get all instances
            individuals = list(self.world.individuals())
            print(f"📊 Instance count: {len(individuals)}")
            
            if not individuals:
                print("⚠️ World has no instances")
                return
            
            # Group instances by type
            instances_by_type = {}
            for ind in individuals:
                type_name = str(type(ind)).split('.')[-1].replace("'>", "")
                if type_name not in instances_by_type:
                    instances_by_type[type_name] = []
                instances_by_type[type_name].append(ind)
            
            # Display instances by type
            for type_name, instances in instances_by_type.items():
                print(f"\n📦 {type_name} ({len(instances)} instances):")
                
                for ind in instances:
                    print(f"  • {ind}")
                    
                    # Display instance properties
                    properties = list(self.world.properties())
                    has_properties = False
                    
                    for prop in properties:
                        if hasattr(ind, prop.python_name):
                            prop_value = getattr(ind, prop.python_name)
                            if prop_value:
                                if not has_properties:
                                    print(f"    🔗 Properties:")
                                    has_properties = True
                                
                                if isinstance(prop_value, list):
                                    if len(prop_value) > 0:
                                        print(f"      {prop.python_name}: {[str(v) for v in prop_value]}")
                                else:
                                    print(f"      {prop.python_name}: {prop_value}")
                    
                    if not has_properties:
                        print(f"    🆓 No properties")
            my_robot = self.world.search_one(iri="*my_robot")
            if my_robot:
                print(f"\n🤖 Robot status:")
                print(f"  • Name: {my_robot}")
                print(f"  • Type: {type(my_robot)}")
                print(f"  • Namespace: {my_robot.namespace}")
                
                # Check holding items
                if hasattr(my_robot, 'isHolding'):
                    holding = getattr(my_robot, 'isHolding')
                    if holding:
                        print(f"  • Holding: {[str(item) for item in holding]}")
                    else:
                        print(f"  • Holding: None")
                
                # Check hand state
                if hasattr(my_robot, 'handIsEmpty'):
                    hand_empty = getattr(my_robot, 'handIsEmpty')
                    print(f"  • Hand is empty: {hand_empty}")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Print world state failed: {e}")
            import traceback
            traceback.print_exc()
