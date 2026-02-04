#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ontology class enumeration script
Calls ontology_loader.py to load all ontologies, finds and prints all class types by namespace classification
Supports BFO definition filtering
"""

import sys
import os
import json
from collections import defaultdict
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from ontology_loader import OntologyLoader


def is_bfo_class(class_uri):
    """Determine if it's a BFO class"""
    bfo_patterns = [
        'http://purl.obolibrary.org/obo/BFO_',
        'obo:BFO_',
        'BFO_',
        '/BFO_'
    ]
    return any(pattern in class_uri for pattern in bfo_patterns)


def extract_namespace_and_name(class_uri):
    """
    Extract namespace and class name from class URI
    Handle various URI formats
    """
    class_uri = str(class_uri).strip()
    
    # Handle owlready2's special format (e.g. "obo.BFO_0000001")
    if class_uri.startswith('obo.'):
        return "http://purl.obolibrary.org/obo/", class_uri[4:]  # Remove "obo." prefix
    
    # Handle standard HTTP URI
    if class_uri.startswith('http://') or class_uri.startswith('https://'):
        if '#' in class_uri:
            namespace = class_uri.rsplit('#', 1)[0] + '#'
            class_name = class_uri.rsplit('#', 1)[1]
        elif '/' in class_uri:
            namespace = class_uri.rsplit('/', 1)[0] + '/'
            class_name = class_uri.rsplit('/', 1)[1]
        else:
            namespace = "Unknown namespace"
            class_name = class_uri
    # Handle other formats
    elif ':' in class_uri and not class_uri.startswith('file:'):
        # Handle prefix format like "prefix:LocalName"
        parts = class_uri.split(':', 1)
        namespace = f"{parts[0]}:"
        class_name = parts[1]
    else:
        namespace = "Unknown namespace"
        class_name = class_uri
    
    return namespace, class_name


def list_all_classes(filter_bfo=True):
    """
    Load all ontologies and list all classes by namespace classification
    
    Args:
        filter_bfo: Whether to filter out BFO classes
    """
    
    print("=" * 60)
    print("🔍 Ontology Class Enumeration Tool")
    if filter_bfo:
        print("🚫 BFO filtering enabled")
    print("=" * 60)
    
    # Create ontology loader instance
    loader = OntologyLoader()
    
    # List available ontology mappings
    loader.list_available_ontologies()
    
    print("\n" + "=" * 60)
    print("📦 Starting to load all ontologies...")
    print("=" * 60)
    
    # Load all ontologies
    try:
        world, main_onto = loader.load_all_ontologies()
        
        print("\n" + "=" * 60)
        print("📋 Directly traversing classes in all ontologies")
        print("=" * 60)
        
        # Directly traverse method, avoiding SPARQL query issues
        namespace_classes = defaultdict(list)
        total_found = 0
        total_filtered = 0
        
        print("🔍 Traversing all ontologies...")
        
        # Correctly get ontology objects
        for ontology_iri in world.ontologies:
            try:
                print(f"\n📄 Checking ontology: {ontology_iri}")
                
                # Get ontology object
                ontology = world.get_ontology(ontology_iri)
                
                # Get all classes in the ontology
                classes = list(ontology.classes())
                
                if classes:
                    print(f"   Found {len(classes)} classes")
                    
                    for cls in classes:
                        total_found += 1
                        
                        # Get basic class information
                        class_iri = cls.iri if hasattr(cls, 'iri') else str(cls)
                        class_name = cls.name if hasattr(cls, 'name') else str(cls).split('.')[-1]
                        
                        # Check if it's a BFO class
                        if filter_bfo and is_bfo_class(class_iri):
                            total_filtered += 1
                            print(f"   🚫 Filtered BFO class: {class_name}")
                            continue
                        
                        # Extract namespace and class name
                        namespace, clean_name = extract_namespace_and_name(class_iri)
                        
                        # Get label
                        label = "No label"
                        if hasattr(cls, 'label') and cls.label:
                            label = str(cls.label[0]) if isinstance(cls.label, list) else str(cls.label)
                        
                        # Get comment
                        comment = ""
                        if hasattr(cls, 'comment') and cls.comment:
                            comment = str(cls.comment[0]) if isinstance(cls.comment, list) else str(cls.comment)
                        
                        # Get parent class information
                        parents = []
                        if hasattr(cls, 'is_a'):
                            for parent in cls.is_a:
                                if hasattr(parent, 'name'):
                                    parents.append(parent.name)
                                elif hasattr(parent, 'iri'):
                                    parents.append(str(parent.iri))
                        
                        namespace_classes[namespace].append({
                            'uri': class_iri,
                            'name': clean_name,
                            'label': label,
                            'comment': comment,
                            'parents': parents
                        })
                else:
                    print("   No classes found")
                    
            except Exception as inner_e:
                print(f"   ❌ Failed to process ontology: {inner_e}")
        
        # Print results
        print("\n" + "=" * 80)
        print("📊 Detailed Results")
        print("=" * 80)
        
        total_classes = 0
        
        for namespace, classes in namespace_classes.items():
            if classes:  # Only show namespaces with classes
                print(f"\n🏷️  namespace: {namespace}")
                print(f"   Class count: {len(classes)}")
                print("   " + "-" * 50)
                
                for cls_info in sorted(classes, key=lambda x: x['name']):
                    # Get basic class information
                    class_name = cls_info['name']
                    class_iri = cls_info['uri']
                    class_label = cls_info['label']
                    
                    print(f"   📝 {class_name}")
                    print(f"      IRI: {class_iri}")
                    print(f"      Label: {class_label}")
                    
                    # Try to get more information (if possible)
                    try:
                        # Get class object through owlready2
                        cls_obj = world.search_one(iri=class_iri)
                        if cls_obj and hasattr(cls_obj, 'is_a'):
                            parents = [p.name for p in cls_obj.is_a if hasattr(p, 'name')]
                            parents_str = ", ".join(parents) if parents else "None"
                            print(f"      Parent classes: {parents_str}")
                            
                            if hasattr(cls_obj, 'comment') and cls_obj.comment:
                                comments = [str(comment) for comment in cls_obj.comment]
                                if comments:
                                    print(f"      Comments: {', '.join(comments)}")
                    except:
                        pass  # Skip if retrieval fails
                    
                    print()
                
                total_classes += len(classes)
        
        # Statistical information
        print("=" * 80)
        print("📈 Statistical Information")
        print("=" * 80)
        print(f"Total namespace count: {len(namespace_classes)}")
        print(f"Namespaces with classes count: {len([ns for ns, classes in namespace_classes.items() if classes])}")
        print(f"Total class count: {total_classes}")
        
        # Show class count statistics by namespace
        print(f"\n📊 Class count by namespace:")
        for namespace, classes in sorted(namespace_classes.items(), key=lambda x: len(x[1]), reverse=True):
            if classes:
                print(f"   {len(classes):3d} classes - {namespace}")
        
        # Save to JSON file
        print("\n" + "=" * 80)
        print("💾 Saving results to JSON file")
        print("=" * 80)
        
        # Prepare JSON data
        json_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_namespaces": len(namespace_classes),
                "namespaces_with_classes": len([ns for ns, classes in namespace_classes.items() if classes]),
                "total_classes": total_classes
            },
            "namespaces": {}
        }
        
        # Convert data format
        for namespace, classes in namespace_classes.items():
            if classes:  # Only save namespaces with classes
                json_data["namespaces"][namespace] = {
                    "class_count": len(classes),
                    "classes": classes
                }
        
        # Compare with history to find newly added classes
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "ontology_classes.json")
        history_file = os.path.join(output_dir, "ontology_classes_history.json")
        new_classes = []
        
        # Read historical records
        historical_classes = set()
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    for ns, ns_data in history_data.get('namespaces', {}).items():
                        for cls in ns_data.get('classes', []):
                            historical_classes.add(cls['uri'])
                print(f"📖 Read historical records: {len(historical_classes)} known classes")
            except Exception as e:
                print(f"⚠️ Failed to read historical records: {e}")
        else:
            print("📝 First run, all classes are new additions")
        
        # Find newly added classes
        current_classes = set()
        for namespace, classes in namespace_classes.items():
            for cls in classes:
                current_classes.add(cls['uri'])
                if cls['uri'] not in historical_classes:
                    new_classes.append({
                        'uri': cls['uri'],
                        'name': cls['name'],
                        'namespace': namespace,
                        'label': cls['label'],
                        'comment': cls['comment']
                    })
        
        # Add new class information to metadata
        json_data['metadata']['new_classes_count'] = len(new_classes)
        json_data['metadata']['historical_classes_count'] = len(historical_classes)
        
        # Save new class list
        new_classes_file = os.path.join(output_dir, "new_classes.json")
        with open(new_classes_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'count': len(new_classes),
                'classes': new_classes
            }, f, ensure_ascii=False, indent=2)
        
        if len(new_classes) > 0:
            print(f"🆕 Found {len(new_classes)} new classes")
            print(f"📄 New class list saved to: {new_classes_file}")
        else:
            print("✅ No new classes found")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Results saved to: {output_file}")
            print(f"📄 File size: {os.path.getsize(output_file)} bytes")
            
            # Save current data as historical record (for next comparison)
            import shutil
            shutil.copy2(output_file, history_file)
            print(f"📚 Historical record updated: {history_file}")
        except Exception as e:
            print(f"❌ Failed to save JSON file: {e}")
        
    except Exception as e:
        print(f"❌ Error occurred while loading ontologies: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    list_all_classes()
