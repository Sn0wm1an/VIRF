#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class creator - responsible for creating new ontology classes
"""

from typing import Dict, Any, List
from owlready2 import Thing
from .base_writer import BaseOntologyWriter


class ClassCreator(BaseOntologyWriter):
    """Class creator - responsible for creating new ontology classes"""
    
    def create_new_classes(self, analysis_data: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
        """Create new classes using owlready2"""
        result = {
            "operation": "create_new_classes_owlready2",
            "classes_created": [],
            "status": "completed"
        }
        
        try:
            missing_items = analysis_data.get('missing_items_analysis', {})
            objects_analysis = missing_items.get('objects', {})
            items_analysis = objects_analysis.get('items_analysis', [])
            
            if debug:
                print(f"\n📝 [DEBUG] Create {len(items_analysis)} new classes using owlready2")
            
            # Get object ontology
            object_onto = self.ontologies.get('object')
            if not object_onto:
                raise Exception("object ontology not loaded")
            
            with object_onto:
                for item in items_analysis:
                    class_name = item.get('name', '')
                    placement = item.get('placement_recommendation', {})
                    new_class_def = placement.get('new_class_definition', {})
                    
                    if not class_name:
                        continue
                    
                    # Get label and comment
                    label = new_class_def.get('label', class_name)
                    comment = new_class_def.get('comment', f'Object class for {class_name}')
                    
                    if debug:
                        print(f"  🏗️ [DEBUG] Create class: {class_name}")
                    
                    # Create class using owlready2
                    new_class = type(class_name, (Thing,), {})
                    new_class.label = [label]
                    new_class.comment = [comment]
                    
                    # Add parent class relationship
                    subclass_of = new_class_def.get('subClassOf', ['PhysicalObject'])
                    if isinstance(subclass_of, str):
                        subclass_of = [subclass_of]
                    
                    for parent_name in subclass_of:
                        parent_class = self.get_class_by_name(parent_name)
                        if parent_class:
                            new_class.is_a.append(parent_class)
                    
                    # Generate corresponding XML representation (for manual appending)
                    from .owl_generator import OWLXMLGenerator
                    generator = OWLXMLGenerator()
                    class_xml = generator.generate_class_xml(class_name, label, comment, subclass_of)
                    self.new_classes_xml.append(class_xml)
                    
                    result["classes_created"].append({
                        "name": class_name,
                        "label": label,
                        "parents": subclass_of
                    })
                    
                    if debug:
                        print(f"    ✅ [DEBUG] Class created successfully: {class_name}")
            
            if debug:
                print(f"✅ [DEBUG] Successfully created {len(result['classes_created'])} items new classes")
                
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            if debug:
                print(f"❌ [DEBUG] New class creation failed: {e}")
        
        return result
