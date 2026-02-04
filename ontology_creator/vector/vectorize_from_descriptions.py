#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Based on LLM description vectorization script
Read descriptions from ontology_llm_descriptions.json and perform batch vectorization
"""

import os
import json
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime


def vectorize_from_descriptions():
    """Based on LLM description vectorization"""
    
    print("🚀 Start LLM description vectorization...")
    print("=" * 60)
    
    # Read LLM description file
    descriptions_file = os.path.join('output', 'ontology_llm_descriptions.json')
    if not os.path.exists(descriptions_file):
        print("❌ ontology_llm_descriptions.json not found, please run generate_llm_descriptions.py first")
        return
    
    with open(descriptions_file, 'r', encoding='utf-8') as f:
        descriptions_data = json.load(f)
    
    print(f"📚 Load descriptions: {len(descriptions_data['classes'])} items classes, {len(descriptions_data['properties'])} items properties")
    
    # Load model
    # Get project root directory cache path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_dir = os.path.join(project_root, '.cache', 'sentence-transformers_all-MiniLM-L6-v2')
    
    if not os.path.exists(model_dir):
        print(f"❌ Model directory not found: {model_dir}")
        print("Please run: python download_model.py")
        return
    
    print(f"📁 Using local model: {model_dir}")
    model = SentenceTransformer(model_dir, device='cuda')
    
    vectors = {}
    
    # Prepare class text
    print("\n📝 Prepare class vectorization text...")
    class_texts = []
    class_items = []
    
    for uri, class_desc in descriptions_data['classes'].items():
        # Combine text: name + label + comment + LLM description
        text_parts = [class_desc['name']]
        
        if class_desc.get('label'):
            text_parts.append(class_desc['label'])
        
        if class_desc.get('comment'):
            text_parts.append(class_desc['comment'])
        
        if class_desc.get('llm_description'):
            text_parts.append(class_desc['llm_description'])
        
        combined_text = ' '.join(text_parts)
        class_texts.append(combined_text)
        
        # Save class information
        class_item = {
            'uri': uri,
            'name': class_desc['name'],
            'label': class_desc.get('label', ''),
            'comment': class_desc.get('comment', ''),
            'namespace': class_desc.get('namespace', ''),
            'llm_description': class_desc.get('llm_description', ''),
            'text': combined_text
        }
        class_items.append(class_item)
    
    # Prepare property text
    print("📝 Prepare property vectorization text...")
    property_texts = []
    property_items = []
    
    for uri, prop_desc in descriptions_data['properties'].items():
        # Combine text: name + label + comment + LLM description
        text_parts = [prop_desc['name']]
        
        if prop_desc.get('label'):
            text_parts.append(prop_desc['label'])
        
        if prop_desc.get('comment'):
            text_parts.append(prop_desc['comment'])
        
        if prop_desc.get('llm_description'):
            text_parts.append(prop_desc['llm_description'])
        
        combined_text = ' '.join(text_parts)
        property_texts.append(combined_text)
        
        # Save property information
        property_item = {
            'uri': uri,
            'name': prop_desc['name'],
            'label': prop_desc.get('label', ''),
            'comment': prop_desc.get('comment', ''),
            'namespace': prop_desc.get('namespace', ''),
            'domain': prop_desc.get('domain', ''),
            'range': prop_desc.get('range', ''),
            'llm_description': prop_desc.get('llm_description', ''),
            'text': combined_text
        }
        property_items.append(property_item)
    
    # Batch vectorization
    all_texts = class_texts + property_texts
    print(f"\n🔄 Batch vectorization {len(all_texts)} items...")
    
    if all_texts:
        embeddings = model.encode(all_texts, show_progress_bar=True)
        
        # Separate class and property vectors
        class_embeddings = embeddings[:len(class_texts)]
        property_embeddings = embeddings[len(class_texts):]
        
        # Organize vector data
        print("\n📦 Organize vector data...")
        
        # Organize class vectors by namespace
        for i, class_item in enumerate(class_items):
            namespace = class_item['namespace']
            if namespace not in vectors:
                vectors[namespace] = []
            
            class_item['vector'] = class_embeddings[i].tolist()
            vectors[namespace].append(class_item)
        
        # Organize property vectors by namespace
        for i, property_item in enumerate(property_items):
            namespace = property_item['namespace']
            if namespace not in vectors:
                vectors[namespace] = []
            
            property_item['vector'] = property_embeddings[i].tolist()
            vectors[namespace].append(property_item)
    
    # Save vectorization results
    print("\n💾 Save vectorization results...")
    
    # Save as JSON format
    output_json = os.path.join('output', 'ontology_vectors.json')
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'model': 'all-MiniLM-L6-v2',
        'total_classes': len(descriptions_data['classes']),
        'total_properties': len(descriptions_data['properties']),
        'total_vectors': len(vectors)
    }
    json_data = {
        'metadata': metadata,
        'vectors': vectors
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # Save as pickle format (faster loading)
    output_pickle = os.path.join('output', 'ontology_vectors.pkl')
    with open(output_pickle, 'wb') as f:
        pickle.dump(vectors, f)
    
    print("\n" + "=" * 60)
    print("📊 Vectorization statistics")
    print("=" * 60)
    print(f"Total items: {len(vectors)}")
    print(f"  - Classes: {len(descriptions_data['classes'])}")
    print(f"  - Properties: {len(descriptions_data['properties'])}")
    print(f"Vector dimension: 384")
    print(f"Model: all-MiniLM-L6-v2")
    
    print(f"\n📋 Namespace statistics:")
    for namespace, items in vectors.items():
        class_count = sum(1 for item in items if 'domain' not in item)
        prop_count = sum(1 for item in items if 'domain' in item)
        print(f"   {len(items):3d} items ({class_count} classes + {prop_count} properties) - {namespace}")
    
    print(f"\n✅ Vectorization completed!")
    print(f"📄 JSON file: {output_json}")
    print(f"📦 Pickle file: {output_pickle}")


if __name__ == "__main__":
    vectorize_from_descriptions()
