#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vectorization test script
Generate test JSON file and perform vectorization comparison test
"""

import json
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def generate_test_data():
    """Generate test JSON file"""
    
    # Create output directory
    output_dir = os.path.join('output', 'vector')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate test data based on ontology classes
    test_data = {
        "Fork": {
            "standard_terms": ["fork", "eating fork", "dinner fork"],
            "related_terms": ["tableware", "cutlery", "utensil", "dining tool"],
            "similar_terms": ["spoon", "knife", "chopsticks", "spork"],
            "unrelated_terms": ["plate", "microwave", "book", "car"]
        },
        "Knife": {
            "standard_terms": ["knife", "kitchen knife", "cutting knife"],
            "related_terms": ["cutting tool", "blade", "kitchen utensil", "sharp tool"],
            "similar_terms": ["scissors", "razor", "cleaver", "scalpel"],
            "unrelated_terms": ["fork", "cup", "television", "chair"]
        },
        "Microwave": {
            "standard_terms": ["microwave", "microwave oven", "microwave appliance"],
            "related_terms": ["kitchen appliance", "heating device", "cooking equipment", "electrical appliance"],
            "similar_terms": ["oven", "toaster", "rice cooker", "stove"],
            "unrelated_terms": ["refrigerator", "washing machine", "fork", "book"]
        },
        "Pot": {
            "standard_terms": ["pot", "cooking pot", "saucepan"],
            "related_terms": ["cookware", "container", "kitchen utensil", "cooking vessel"],
            "similar_terms": ["pan", "bowl", "kettle", "casserole"],
            "unrelated_terms": ["fork", "microwave", "phone", "clothing"]
        },
        "Cup": {
            "standard_terms": ["cup", "drinking cup", "beverage cup"],
            "related_terms": ["container", "tableware", "drinkware", "vessel"],
            "similar_terms": ["mug", "glass", "bowl", "tumbler"],
            "unrelated_terms": ["knife", "pot", "television", "car"]
        }
    }
    
    # Save test data
    test_data_path = os.path.join(output_dir, 'test_data.json')
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Test data generated: {test_data_path}")
    return test_data

def load_ontology_vectors():
    """Load ontology vectors"""
    
    output_dir = os.path.join('output', 'vector')
    
    # Load Pickle file first
    pkl_path = os.path.join(output_dir, 'ontology_vectors.pkl')
    if os.path.exists(pkl_path):
        with open(pkl_path, 'rb') as f:
            return pickle.load(f)
    
    # Load JSON file as backup
    json_path = os.path.join(output_dir, 'ontology_vectors.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return None

def load_model():
    """Load local model"""
    cache_dir = os.path.join(os.getcwd(), '.cache')
    model_dir = os.path.join(cache_dir, 'sentence-transformers_all-MiniLM-L6-v2')
    
    if not os.path.exists(model_dir):
        print("❌ Model not found, please run download_model.py first")
        return None
    
    return SentenceTransformer(model_dir, device='cpu')

def find_ontology_class(vectors, class_name):
    """Find specified class in ontology vectors"""
    for namespace, classes in vectors.items():
        for cls in classes:
            if cls['name'] == class_name:
                return cls
    return None

def test_vectorization():
    """Test vectorization effect"""
    
    print("🧪 Start vectorization test")
    print("=" * 60)
    
    # Generate test data
    test_data = generate_test_data()
    
    # Load model and vectors
    model = load_model()
    if not model:
        return
    
    vectors = load_ontology_vectors()
    if not vectors:
        print("❌ Ontology vectors not found, please run vectorize_ontology.py first")
        return
    
    print("📊 Start similarity test")
    print("=" * 60)
    
    # Test each class
    for class_name, test_terms in test_data.items():
        print(f"\n🔍 Test class: {class_name}")
        print("-" * 40)
        
        # Find corresponding class in ontology
        ontology_class = find_ontology_class(vectors, class_name)
        if not ontology_class:
            print(f"❌ Class not found in ontology: {class_name}")
            continue
        
        # Get ontology class vector
        ontology_vector = np.array(ontology_class['vector']).reshape(1, -1)
        print(f"📝 Class description: {ontology_class['text']}")
        
        # Test similarity of various terms
        for term_type, terms in test_terms.items():
            print(f"\n📋 {term_type}:")
            
            similarities = []
            for term in terms:
                # Generate test term vector
                test_vector = model.encode(term).reshape(1, -1)
                
                # Calculate cosine similarity
                similarity = cosine_similarity(ontology_vector, test_vector)[0][0]
                similarities.append((term, similarity))
                
                print(f"   {term}: {similarity:.4f}")
            
            # Calculate average similarity
            avg_similarity = np.mean([s[1] for s in similarities])
            print(f"   Average similarity: {avg_similarity:.4f}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed")

if __name__ == "__main__":
    test_vectorization()
