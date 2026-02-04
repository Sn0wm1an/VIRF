#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABox to TBox Mapper
Processes JSON input, precisely matches class and relation names, creates corresponding assertions and returns mapped TBox
"""

import json
import owlready2 as owl
from typing import Dict, List, Optional, Any, Tuple

# Try different import paths
try:
    from .ontology_loader import OntologyLoader
except ImportError:
    try:
        from ontology_loader import OntologyLoader
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from ontology_loader import OntologyLoader


class ABoxTBoxMapper:
    """ABox to TBox Mapper class"""
    
    def __init__(self, world: owl.World, main_ontology: owl.Ontology, verbose: bool = False):
        """
        Initialize mapper
        
        Args:
            world: OWL World instance
            main_ontology: Main ontology instance
            verbose: Whether to enable detailed logging
        """
        self.world = world
        self.main_ontology = main_ontology
        self.verbose = verbose
        self.tbox_cache = {}  # Cache TBox elements
        self.created_instances = {}  # Created instances
        
        # Preload TBox elements
        self._preload_tbox_elements()
    
    def _preload_tbox_elements(self):
        """Preload all TBox elements (classes, properties, states, etc.)"""
        
        # Load all classes
        self.tbox_cache['classes'] = {}
        for cls in self.world.classes():
            self.tbox_cache['classes'][cls.name] = cls
        
        # Load all properties
        self.tbox_cache['properties'] = {}
        for prop in self.world.properties():
            self.tbox_cache['properties'][prop.name] = prop
        
        # Load all states (OnState, OffState, etc.)
        self.tbox_cache['states'] = {}
        for cls in self.world.classes():
            if 'state' in cls.name.lower() or cls.name in ['OnState', 'OffState', 'StandbyState']:
                self.tbox_cache['states'][cls.name] = cls
        
    
    def get_tbox_element(self, name: str, element_type: str) -> Optional[Any]:
        """
        Get TBox element, using world.search method to support cross-namespace search
        
        Args:
            name: Element name
            element_type: Element type ('class', 'property', 'state')
            
        Returns:
            TBox element object, return None if not found
        """
        try:
            if element_type == 'class':
                # Search for classes, ensure found items are classes not instances
                candidates = list(self.world.search(iri=f"*{name}"))
                for candidate in candidates:
                    # Check if it's a class (callable and has __name__ attribute)
                    if hasattr(candidate, '__call__') and hasattr(candidate, '__name__'):
                        return candidate
                
                # If not found, try search_one
                candidate = self.world.search_one(iri=f"*{name}")
                if candidate and hasattr(candidate, '__call__'):
                    return candidate
                    
            elif element_type == 'property':
                # Special handling: prioritize searching for common relation properties from relation ontology
                if name in ['contains', 'hasMaterial', 'hasState']:
                    preferred_candidate = self.world.search_one(iri=f"*relation#{name}")
                    if preferred_candidate and hasattr(preferred_candidate, 'domain'):
                        return preferred_candidate
                
                # General property search
                candidate = self.world.search_one(iri=f"*{name}")
                if candidate and hasattr(candidate, 'domain'):
                    return candidate
                    
            elif element_type == 'state':
                # Search for state classes
                candidates = list(self.world.search(iri=f"*{name}"))
                for candidate in candidates:
                    if hasattr(candidate, '__call__') and hasattr(candidate, '__name__'):
                        # Additional check if it's a state class
                        if 'state' in candidate.name.lower() or candidate.name in ['OnState', 'OffState', 'StandbyState']:
                            return candidate
                        # Accept if name matches exactly
                        if candidate.name == name:
                            return candidate
            
            
            if self.verbose:
                print(f"❌ Class not found: {name}")
            return None
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error searching TBox element: {name} ({element_type}) - {e}")
            return None
    
    def create_instance(self, class_name: str, instance_name: str, properties: Dict[str, Any] = None) -> Optional[Any]:
        """
        Create class instance
        
        Args:
            class_name: Class name
            instance_name: Instance name
            properties: Property dictionary
            
        Returns:
            Created instance or None
        """
        # First check if already created
        if instance_name in self.created_instances:
            return self.created_instances[instance_name]
        
        # Get class definition object
        cls = self.get_tbox_element(class_name, 'class')
        if not cls:
            return None
        
        # Determine target ontology (prefer kitchen-axioms)
        target_onto = self.main_ontology
        
        # If not specified or failed to get, try using kitchen-axioms ontology
        if not target_onto:
            try:
                kitchen_axioms_onto = self.world.get_ontology("http://purl.obolibrary.org/obo/domain/kitchen-axioms")
                if kitchen_axioms_onto:
                    target_onto = kitchen_axioms_onto
            except:
                pass
        
        # Create instance
        try:
            with target_onto:
                instance = cls(instance_name)
                self.created_instances[instance_name] = instance
                
                # Initialize isLocated property to false (all physical objects are not located by default)
                if self._is_physical_object(instance):
                    self._initialize_islocated_property(instance)
                
                if properties:
                    for prop_name, value in properties.items():
                        prop = self.get_tbox_element(prop_name, 'property')
                        if prop:
                            setattr(instance, prop.python_name, value)
                            if self.verbose:
                                print(f"  🔗 Setting property: {prop_name} = {value}")
                
                if self.verbose:
                    print(f"✅ Created instance: {instance_name} (type: {class_name})")
                return instance
        except Exception as e:
            return None

    def _is_physical_object(self, instance) -> bool:
        """Check if instance is a subclass of PhysicalObject"""
        try:
            # Find PhysicalObject class
            physical_object_class = self.world.search_one(iri="*PhysicalObject")
            if not physical_object_class:
                return False
            
            # Check if instance's class is a subclass of PhysicalObject
            for cls in instance.is_a:
                if cls == physical_object_class or physical_object_class in cls.ancestors():
                    return True
            return False
        except Exception as e:
            return False

    def _initialize_islocated_property(self, instance):
        """Initialize object's isLocated property to false"""
        try:
            # **Force use of isLocated property from action-safety-axioms namespace**
            action_safety_islocated = self.world.search_one(iri="http://purl.obolibrary.org/obo/domain/action-safety-axioms#isLocated")
            
            if action_safety_islocated:
                # Set isLocated property to false (data property directly sets value, no list needed)
                setattr(instance, action_safety_islocated.python_name, False)
            else:
                # Fallback: search for any isLocated property
                is_located_prop = self.world.search_one(iri="*isLocated")
                if is_located_prop:
                    setattr(instance, is_located_prop.python_name, False)
                else:
                    pass
        except Exception as e:
            pass
    
    
    def create_assertion(self, subject_name: str, property_name: str, 
                        object_name: str, assertion_type: str = 'relation') -> bool:
        """
        Create assertion
        
        Args:
            subject_name: Subject instance name
            property_name: Property name (exact match)
            object_name: Object instance name or state name
            assertion_type: Assertion type ('relation', 'state', 'material')
            
        Returns:
            Whether assertion creation was successful
        """
        # Get subject instance
        if subject_name not in self.created_instances:
            return False
        
        subject_instance = self.created_instances[subject_name]
        
        # Get property
        property_obj = self.get_tbox_element(property_name, 'property')
        if not property_obj:
            return False
        
        # Process object based on assertion type
        object_value = None
        object_type = None

        # Check if object_name is a dictionary (new format)
        if isinstance(object_name, dict):
            object_value = object_name.get('value')
            object_type = object_name.get('type')
        else:
            # Compatible with old format, default to instance
            object_value = object_name
            object_type = assertion_type # Use passed assertion_type as default type

        object_instance = None

        if object_type == 'literal':
            # Literal assertion: object is a literal value
            object_instance = object_value
        
        elif object_type == 'state':
            # State assertion: object is a state class
            
            # Check if already created
            if object_value in self.created_instances:
                object_instance = self.created_instances[object_value]
            else:
                state_cls = self.get_tbox_element(object_value, 'state')
                if state_cls:
                    # Create state instance, ensure in same namespace as subject
                    state_instance_name = f"{object_value}_for_{subject_name}"
                    if state_instance_name not in self.created_instances:
                        try:
                            if self.verbose:
                                print(f"  🔗 Creating state instance: {state_instance_name}")
                            # Get subject instance's namespace
                            subject_namespace = subject_instance.namespace
                            
                            # Create state instance in subject's namespace
                            with subject_namespace.ontology:
                                object_instance = state_cls(state_instance_name)
                                self.created_instances[state_instance_name] = object_instance
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            return False
                    else:
                        object_instance = self.created_instances[state_instance_name]
        
        elif object_type == 'type':
            # Type assertion: object is a class object
            type_cls = self.get_tbox_element(object_value, 'class')
            if type_cls:
                object_instance = type_cls
            else:
                return False
    
        elif object_type in ['relation', 'material', 'instance', 'spatial']: # Add spatial type support
            # Relation assertion: object is another instance
            if object_value not in self.created_instances:
                return False
            object_instance = self.created_instances[object_value]
            
            # Special handling for spatial relations
        
        if object_instance is None:
            return False
        
        # Create assertion
        try:
            
            # Check if property exists
            if hasattr(subject_instance, property_obj.python_name): # Use python_name
                attr = getattr(subject_instance, property_obj.python_name)
                
                # 🔑 Improved property assignment logic
                if isinstance(attr, owl.prop.IndividualValueList): # Check if it's a multi-value property
                    # For spatial relations, check if already exists to avoid duplicates
                    if object_type == 'spatial' and object_instance in attr:
                        return True
                    
                    attr.append(object_instance)
                    return True
                elif hasattr(attr, 'append'):
                    # Handle possible list properties
                    if object_type == 'spatial' and object_instance in attr:
                        return True
                    attr.append(object_instance)
                    return True
                else:
                    # Try direct assignment or create list
                    if object_type == 'spatial':
                        # Spatial relations are usually multi-valued
                        setattr(subject_instance, property_obj.python_name, [object_instance])
                    else:
                        setattr(subject_instance, property_obj.python_name, object_instance)
                    return True
            else:
                return False
        except Exception as e:
            return False  
    
    def process_json_mapping(self, json_data: Dict) -> Dict[str, Any]:
        """
        Process JSON mapping data, create ABox assertions
        
        Args:
            json_data: JSON mapping data
            
        Returns:
            Processing result dictionary
        """
        
        result = {
            'success': True,
            'created_instances': [],
            'created_assertions': [],
            'errors': [],
            'tbox_mapping': {}
        }
        
        try:
            # 1. Process instance creation
            instances_data = json_data.get('instances', [])
            
            for instance_data in instances_data:
                class_name = instance_data.get('class_name')
                instance_name = instance_data.get('instance_name')
                target_ontology = instance_data.get('target_ontology')  # Optional field
                properties = instance_data.get('properties')  # Optional field
                
                if not class_name or not instance_name:
                    error_msg = f"Instance data missing required fields (class_name, instance_name): {instance_data}"
                    result['errors'].append(error_msg)
                    continue
                
                # Create instance
                instance = self.create_instance(class_name, instance_name, properties)
                if instance:
                    result['created_instances'].append({
                        'name': instance_name,
                        'class': class_name,
                        'ontology': target_ontology or 'kitchen-axioms (default)'
                    })
                    if self.verbose:
                        print(f"✅ Created instance: {instance_name} (type: {class_name})")
                else:
                    error_msg = f"Instance creation failed: {instance_name} ({class_name})"
                    result['errors'].append(error_msg)
            
            # 2. Process assertion creation
            assertions_data = json_data.get('assertions', [])
            
            for assertion_data in assertions_data:
                subject = assertion_data.get('subject')
                property_name = assertion_data.get('property')
                object_name = assertion_data.get('object')
                assertion_type = assertion_data.get('type', 'relation')
                
                if not all([subject, property_name, object_name]):
                    error_msg = f"Assertion data incomplete: {assertion_data}"
                    result['errors'].append(error_msg)
                    pass
                    continue
                
                success = self.create_assertion(subject, property_name, object_name, assertion_type)
                if success:
                    result['created_assertions'].append({
                        'subject': subject,
                        'property': property_name,
                        'object': object_name,
                        'type': assertion_type
                    })
                else:
                    error_msg = f"Assertion creation failed: {subject}.{property_name} = {object_name}"
                    result['errors'].append(error_msg)
            
            # 3. Generate TBox mapping summary
            result['tbox_mapping'] = {
                'classes_used': list(set([inst['class'] for inst in result['created_instances']])),
                'properties_used': list(set([ass['property'] for ass in result['created_assertions']])),
                'total_instances': len(result['created_instances']),
                'total_assertions': len(result['created_assertions'])
            }
            
            if result['errors']:
                result['success'] = False
                pass
            
        except Exception as e:
            result['success'] = False
            error_msg = f"JSON mapping processing exception: {e}"
            result['errors'].append(error_msg)
            pass
        
        return result
    
    def get_tbox_summary(self) -> Dict[str, Any]:
        """
        Get TBox summary information
        
        Returns:
            TBox summary dictionary
        """
        return {
            'total_classes': len(self.tbox_cache['classes']),
            'total_properties': len(self.tbox_cache['properties']),
            'total_states': len(self.tbox_cache['states']),
            'available_classes': list(self.tbox_cache['classes'].keys()),
            'available_properties': list(self.tbox_cache['properties'].keys()),
            'available_states': list(self.tbox_cache['states'].keys())
        }


# Convenience functions
def create_mapper_from_ontology_uri(ontology_uri: str) -> ABoxTBoxMapper:
    """
    Create mapper from ontology URI
    
    Args:
        ontology_uri: Ontology URI
        
    Returns:
        ABoxTBoxMapper instance
    """
    loader = OntologyLoader()
    main_onto = loader.load_ontology(ontology_uri=ontology_uri)
    world = main_onto.world
    
    return ABoxTBoxMapper(world, main_onto)


def create_mapper_with_all_ontologies(verbose: bool = False) -> ABoxTBoxMapper:
    """
    Load all ontologies and create mapper
    
    Args:
        verbose: Whether to enable detailed logging
        
    Returns:
        ABoxTBoxMapper instance
    """
    loader = OntologyLoader(verbose=verbose)
    world, main_onto = loader.load_all_ontologies()
    
    return ABoxTBoxMapper(world, main_onto, verbose=verbose)


# Usage example
if __name__ == "__main__":
    print("🧪 ABox to TBox Mapper Test")
    
    # Create mapper
    mapper = create_mapper_with_all_ontologies()
    
    # Display TBox summary
    tbox_summary = mapper.get_tbox_summary()
    print(f"\n📊 TBox Summary:")
    print(f"  - Class count: {tbox_summary['total_classes']}")
    print(f"  - Property count: {tbox_summary['total_properties']}")
    print(f"  - State count: {tbox_summary['total_states']}")
    
    # Display some key class names for debugging
    print(f"\nKey class name debugging:")
    key_classes = ['Microwave', 'Fork', 'Metal']
    for class_name in key_classes:
        matching_classes = [name for name in tbox_summary['available_classes'] if class_name.lower() in name.lower()]
        print(f"  - Search '{class_name}': {matching_classes if matching_classes else 'Not found'}")
    
    print(f"\n📋 All available class names (first 20):")
    for i, class_name in enumerate(tbox_summary['available_classes'][:20]):
        print(f"  {i+1:2d}. {class_name}")
    
    # Test JSON mapping
    test_json = {
        "instances": [
            {
                "class_name": "Microwave",
                "instance_name": "TestMicrowave_Mapper",
                "target_ontology": "http://purl.obolibrary.org/obo/domain/kitchen-axioms#"
            },
            {
                "class_name": "Fork",
                "instance_name": "TestFork_Mapper"
            },
            {
                "class_name": "Metal",
                "instance_name": "TestMetal_Mapper"
            }
        ],
        "assertions": [
            {
                "subject": "TestFork_Mapper",
                "property": "hasMaterial",
                "object": "TestMetal_Mapper",
                "type": "material"
            },
            {
                "subject": "TestMicrowave_Mapper",
                "property": "containsMetalObject",
                "object": "TestFork_Mapper",
                "type": "relation"
            },
            {
                "subject": "TestMicrowave_Mapper",
                "property": "isOperating",
                "object": "OnState",
                "type": "state"
            }
        ]
    }
    
    # Process mapping
    result = mapper.process_json_mapping(test_json)
    
    print(f"\n📋 Mapping result:")
    print(f"  Success: {result['success']}")
    print(f"  TBox mapping: {result['tbox_mapping']}")
    
    print("\nABox to TBox Mapper test completed")
