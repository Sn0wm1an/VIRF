#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM description generation script
Generate LLM descriptions only for newly added ontology classes and append to description file
"""

import os
import json
import sys
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from llm.llm_service import call_llm


def generate_class_description(class_info):
    """Generate English description for ontology class using LLM"""
    try:
        # Call LLM
        response = call_llm('ontology_class_description', 
                          name=class_info['name'],
                          label=class_info.get('label', 'Not specified'),
                          comment=class_info.get('comment', 'Not specified'),
                          namespace=class_info.get('namespace', 'Not specified'))
        
        if response and isinstance(response, str):
            # Clean response, remove extra spaces and newlines
            description = response.strip().replace('\n', ' ').replace('  ', ' ')
            return description
        else:
            return f"A class named {class_info['name']} in the ontology that represents entities of this type."
    
    except Exception as e:
        print(f"   ⚠️ LLM call failed: {e}")
        # Return default description
        return f"A class named {class_info['name']} in the ontology that represents entities of this type."


def generate_property_description(property_info):
    """Generate English description for ontology property using LLM"""
    try:
        # Call LLM
        response = call_llm('ontology_property_description', 
                          name=property_info['name'],
                          label=property_info.get('label', 'Not specified'),
                          comment=property_info.get('comment', 'Not specified'),
                          domain=property_info.get('domain', 'Not specified'),
                          range=property_info.get('range', 'Not specified'),
                          namespace=property_info.get('namespace', 'Not specified'))
        
        if response and isinstance(response, str):
            # Clean response, remove extra spaces and newlines
            description = response.strip().replace('\n', ' ').replace('  ', ' ')
            return description
        else:
            return f"A relationship property named {property_info['name']} that relates entities in the ontology."
    
    except Exception as e:
        print(f"   ⚠️ LLM call failed: {e}")
        # Return default description
        return f"A relationship property named {property_info['name']} that relates entities in the ontology."


def generate_llm_descriptions():
    """Generate LLM descriptions for newly added ontology classes and properties"""
    
    print("🚀 Starting LLM description generation...")
    print("=" * 60)
    
    # Read ontology class data
    classes_file = os.path.join('output', 'ontology_classes.json')
    if not os.path.exists(classes_file):
        print("❌ ontology_classes.json not found, please run list_ontology_classes.py first")
        return
    
    with open(classes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Read new classes list
    new_classes_file = os.path.join('output', 'new_classes.json')
    new_classes_uris = set()
    
    if os.path.exists(new_classes_file):
        with open(new_classes_file, 'r', encoding='utf-8') as f:
            new_classes_data = json.load(f)
            # Fix data structure reading logic - directly read from classes array
            for cls in new_classes_data.get('classes', []):
                new_classes_uris.add(cls['uri'])
            print(f"🆕 Found {len(new_classes_uris)} new classes to generate descriptions")
    else:
        print("📝 No new classes file found, will generate descriptions for all classes")
    
    # Read existing LLM descriptions
    descriptions_file = os.path.join('output', 'ontology_llm_descriptions.json')
    existing_descriptions = {}
    
    if os.path.exists(descriptions_file):
        with open(descriptions_file, 'r', encoding='utf-8') as f:
            existing_descriptions = json.load(f)
        print(f"📚 Loaded existing descriptions: {len(existing_descriptions.get('classes', {}))} classes, {len(existing_descriptions.get('properties', {}))} properties")
    else:
        existing_descriptions = {
            'classes': {},
            'properties': {},
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        }
    
    # Statistics
    new_class_count = 0
    new_property_count = 0
    skipped_class_count = 0
    skipped_property_count = 0
    
    # 1. Process ontology classes
    print("\n📝 Processing ontology classes...")
    for namespace, namespace_data in data['namespaces'].items():
        for cls in namespace_data['classes']:
            cls_uri = cls['uri']
            
            # Check if description needs to be generated
            should_generate = False
            
            if os.path.exists(new_classes_file):
                # If there is a new classes file, only process new classes
                should_generate = cls_uri in new_classes_uris
            else:
                # If no new classes file (first run), check if there is already a description
                should_generate = cls_uri not in existing_descriptions['classes']
            
            if should_generate:
                print(f"   🆕 Generating description: {cls['name']}")
                
                # Prepare class information
                class_info = cls.copy()
                class_info['namespace'] = namespace
                
                # Generate LLM description
                llm_description = generate_class_description(class_info)
                
                # Save description
                existing_descriptions['classes'][cls_uri] = {
                    'uri': cls_uri,
                    'name': cls['name'],
                    'label': cls.get('label', ''),
                    'comment': cls.get('comment', ''),
                    'namespace': namespace,
                    'llm_description': llm_description,
                    'generated_at': datetime.now().isoformat()
                }
                
                new_class_count += 1
                print(f"      ✅ Description: {llm_description[:100]}...")
            else:
                skipped_class_count += 1
                # Fix misleading prompt information
                if os.path.exists(new_classes_file):
                    print(f"   ♻️ Skipping: {cls['name']} (not in new list)")
                else:
                    print(f"   ♻️ Skipping: {cls['name']} (already has description)")
    
    # 2. Process relation properties
    print("\n📝 Processing relation properties...")
    relation_properties_file = os.path.join('output', 'relation_properties.json')
    
    if os.path.exists(relation_properties_file):
        with open(relation_properties_file, 'r', encoding='utf-8') as f:
            relation_data = json.load(f)
        
        for namespace, namespace_data in relation_data['namespaces'].items():
            for prop in namespace_data['properties']:
                prop_uri = prop['uri']
                
                # Check if description needs to be generated
                if prop_uri not in existing_descriptions['properties']:
                    print(f"   🆕 Generating description: {prop['name']}")
                    
                    # Prepare property information
                    property_info = prop.copy()
                    property_info['namespace'] = namespace
                    
                    # Generate LLM description
                    llm_description = generate_property_description(property_info)
                    
                    # Save description
                    existing_descriptions['properties'][prop_uri] = {
                        'uri': prop_uri,
                        'name': prop['name'],
                        'label': prop.get('label', ''),
                        'comment': prop.get('comment', ''),
                        'namespace': namespace,
                        'domain': prop.get('domain', ''),
                        'range': prop.get('range', ''),
                        'llm_description': llm_description,
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    new_property_count += 1
                    print(f"      ✅ Description: {llm_description[:100]}...")
                else:
                    skipped_property_count += 1
                    print(f"   ♻️ Skipping: {prop['name']} (already has description)")
    
    # Update metadata
    existing_descriptions['metadata']['updated_at'] = datetime.now().isoformat()
    existing_descriptions['metadata']['total_classes'] = len(existing_descriptions['classes'])
    existing_descriptions['metadata']['total_properties'] = len(existing_descriptions['properties'])
    
    # Save updated descriptions file
    with open(descriptions_file, 'w', encoding='utf-8') as f:
        json.dump(existing_descriptions, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("📊 LLM description generation statistics")
    print("=" * 60)
    print(f"New class descriptions generated: {new_class_count}")
    print(f"Classes skipped: {skipped_class_count}")
    print(f"New property descriptions generated: {new_property_count}")
    print(f"Properties skipped: {skipped_property_count}")
    print(f"Total class descriptions: {len(existing_descriptions['classes'])}")
    print(f"Total property descriptions: {len(existing_descriptions['properties'])}")
    print(f"\n✅ LLM descriptions saved to: {descriptions_file}")


if __name__ == "__main__":
    generate_llm_descriptions()
