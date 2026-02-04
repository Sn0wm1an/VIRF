#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relation property list generation script
Extract all relation properties from the ontology, support incremental detection of new properties
"""

import os
import json
import sys
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from ontology_loader import OntologyLoader


def list_relation_properties():
    """Extract and list all relation properties"""
    
    print("🔍 Start extracting relation properties...")
    print("=" * 60)
    
    # Load ontology
    loader = OntologyLoader()
    try:
        world, main_onto = loader.load_all_ontologies()
        print("✅ Ontology loaded successfully")
    except Exception as e:
        print(f"❌ Ontology loading failed: {e}")
        return
    
    # Create output directory
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Collect all relation properties
    properties_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_properties': 0
        },
        'namespaces': {}
    }
    
    total_properties = 0
    
    print(f"\n📋 Extracting relation properties...")
    print(f"   Found {len(world.ontologies)} ontologies")
    
    # Correctly traverse ontology objects
    ontology_list = list(world.ontologies.values())
    print(f"   Found {len(ontology_list)} ontology objects")
    
    for i, onto in enumerate(ontology_list):
        print(f"\n🔍 Processing ontology {i+1}/{len(ontology_list)}")
        print(f"   🔍 Ontology type: {type(onto)}")
        print(f"   🔍 Ontology IRI: {onto.base_iri if hasattr(onto, 'base_iri') else 'N/A'}")
        
        # Check if it is a valid ontology object
        if not hasattr(onto, 'object_properties'):
            print(f"   ⏭️ Skipping invalid ontology object: {onto}")
            continue
            
        try:
            namespace = str(onto.base_iri)
            print(f"   📁 namespace: {namespace}")
            
            # Skip BFO ontology
            if 'bfo' in namespace.lower():
                print(f"   🚫 Skipping BFO ontology: {namespace}")
                continue
            
            # Count property number
            obj_props = list(onto.object_properties())
            data_props = list(onto.data_properties())
            print(f"   📊 Object property count: {len(obj_props)}, Data property count: {len(data_props)}")
            
            properties_list = []
            
            # Extract object properties
            for prop in obj_props:
                try:
                    property_info = {
                        'uri': str(prop.iri),
                        'name': prop.name,
                        'label': str(prop.label[0]) if prop.label else '',
                        'comment': str(prop.comment[0]) if prop.comment else '',
                        'type': 'ObjectProperty',
                        'domain': [str(d) for d in prop.domain] if hasattr(prop, 'domain') else [],
                        'range': [str(r) for r in prop.range] if hasattr(prop, 'range') else []
                    }
                    properties_list.append(property_info)
                    print(f"   ✅ ObjectProperty: {prop.name}")
                    
                except Exception as e:
                    print(f"   ⚠️ Processing ObjectProperty {prop.name} failed: {e}")
                    continue
            
            # Extract data properties
            for prop in data_props:
                try:
                    property_info = {
                        'uri': str(prop.iri),
                        'name': prop.name,
                        'label': str(prop.label[0]) if prop.label else '',
                        'comment': str(prop.comment[0]) if prop.comment else '',
                        'type': 'DataProperty',
                        'domain': [str(d) for d in prop.domain] if hasattr(prop, 'domain') else [],
                        'range': [str(r) for r in prop.range] if hasattr(prop, 'range') else []
                    }
                    properties_list.append(property_info)
                    print(f"   ✅ DataProperty: {prop.name}")
                    
                except Exception as e:
                    print(f"   ⚠️ Processing DataProperty {prop.name} failed: {e}")
                    continue
            
            if properties_list:
                properties_data['namespaces'][namespace] = {
                    'properties': properties_list,
                    'count': len(properties_list)
                }
                total_properties += len(properties_list)
                print(f"   📊 namespace {namespace}: {len(properties_list)} items properties")
        
        except Exception as e:
            print(f"   ⚠️ Processing namespace failed: {e}")
            continue
    
    properties_data['metadata']['total_properties'] = total_properties
    
    # Save relation properties list
    properties_file = os.path.join(output_dir, 'relation_properties.json')
    with open(properties_file, 'w', encoding='utf-8') as f:
        json.dump(properties_data, f, ensure_ascii=False, indent=2)
    
    # Detect new properties (compare with history)
    history_file = os.path.join(output_dir, 'relation_properties_history.json')
    new_properties_file = os.path.join(output_dir, 'new_relation_properties.json')
    
    existing_properties = set()
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # Collect history property URIs
            for namespace_data in history_data.get('namespaces', {}).values():
                for prop in namespace_data.get('properties', []):
                    existing_properties.add(prop['uri'])
            
            print(f"\n📚 Loading history records: {len(existing_properties)} items known properties")
        
        except Exception as e:
            print(f"⚠️ Loading history records failed: {e}")
    
    # Detect new properties
    new_properties_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_new_properties': 0
        },
        'new_properties': {}
    }
    
    total_new_properties = 0
    
    for namespace, namespace_data in properties_data['namespaces'].items():
        new_props_in_namespace = []
        
        for prop in namespace_data['properties']:
            if prop['uri'] not in existing_properties:
                new_props_in_namespace.append(prop)
                total_new_properties += 1
        
        if new_props_in_namespace:
            new_properties_data['new_properties'][namespace] = new_props_in_namespace
    
    new_properties_data['metadata']['total_new_properties'] = total_new_properties
    
    # Save new properties list
    with open(new_properties_file, 'w', encoding='utf-8') as f:
        json.dump(new_properties_data, f, ensure_ascii=False, indent=2)
    
    # Update history records
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(properties_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("📊 Relation property extraction completed")
    print("=" * 60)
    print(f"Total properties: {total_properties}")
    print(f"New properties: {total_new_properties}")
    print(f"Output files:")
    print(f"  - {properties_file}")
    print(f"  - {new_properties_file}")
    print(f"  - {history_file}")
    
    if total_new_properties > 0:
        print(f"\n🆕 Found {total_new_properties} new properties:")
        for namespace, props in new_properties_data['new_properties'].items():
            print(f"   {namespace}: {len(props)} items")
            for prop in props[:3]:  # Show only the first 3 items
                print(f"     - {prop['name']} ({prop['type']})")
            if len(props) > 3:
                print(f"     ... and {len(props) - 3} more items")
    
    return total_properties, total_new_properties


if __name__ == "__main__":
    list_relation_properties()
