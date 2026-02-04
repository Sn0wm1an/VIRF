#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pellet reasoning consistency test script
Specialized for testing ontology reasoning consistency
"""

import sys
import os
from pathlib import Path

# Add project root path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_ontology_consistency():
    """Pellet reasoning consistency test"""
    try:
        print("🔍 Start Pellet reasoning consistency test")
        print("=" * 60)
        
        # Import dependencies
        try:
            import owlready2 as owl
            from owlready2 import sync_reasoner_pellet
            from utils.ontology_loader import OntologyLoader
        except ImportError as e:
            print(f"❌ Dependency import failed: {e}")
            print("Please ensure owlready2 and Java are installed")
            return "false"
        
        # Initialize ontology loader
        print("📦 Initialize ontology loader...")
        loader = OntologyLoader()
        
        # List available ontologies
        loader.list_available_ontologies()
        
        # Load all ontologies
        print("\n🌐 Load all ontologies to World...")
        world, main_onto = loader.load_all_ontologies()
        
        if not world:
            print("❌ Ontology loading failed")
            return "false"
            
        print(f"\n✅ Ontology loading completed")
        print(f"📊 Loaded ontologies count: {len(list(world.ontologies))}")
        print(f"🎯 Main ontology: {main_onto.base_iri if main_onto else 'None'}")
        
        # Run Pellet reasoner
        print("\n🤖 Start Pellet reasoner for consistency check...")
        print("⏳ This may take some time, please be patient...")
        
        try:
            with world:
                sync_reasoner_pellet(world, infer_property_values=True, infer_data_property_values=True)
            
            print("\n✅ Reasoning test passed!")
            print("🎉 Ontology logic consistent, no contradictions found")
            
            # Display reasoning statistics
            total_classes = len(list(world.classes()))
            total_properties = len(list(world.properties()))
            total_individuals = len(list(world.individuals()))
            
            print(f"\n📊 Reasoning statistics:")
            print(f"   🏷️  Classes count: {total_classes}")
            print(f"   🔗 Properties count: {total_properties}")
            print(f"   👤 Individuals count: {total_individuals}")
            
            return "success"
            
        except Exception as reasoning_error:
            print(f"\n❌ Reasoning error detected:")
            print(f"🔥 Error details: {reasoning_error}")
            
            # Try to parse error information
            error_str = str(reasoning_error)
            if "Person is not in the definition order" in error_str:
                print("\n💡 Diagnosis suggestions:")
                print("   🔍 Person class definition order error")
                print("   📝 Possible cause: Person class is referenced but not defined correctly")
                print("   🛠️  Solution: Check the definition of Person class in object.owl")
            elif "InternalReasonerException" in error_str:
                print("\n💡 Diagnosis suggestions:")
                print("   🔍 Internal reasoner exception")
                print("   📝 Possible cause: Ontology structure or class hierarchy definition is incorrect")
                print("   🛠️  Solution: Check the class inheritance relationship and definition integrity")
                
            return "false"
    
    except Exception as e:
        print(f"\n💥 Test script execution failed: {e}")
        return "false"

def main():
    """Main function"""
    print("🚀 Pellet reasoning consistency test tool")
    print(f"📁 Work directory: {os.getcwd()}")
    
    success = test_ontology_consistency()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 Test result: ✅ Pass")
        print("🎉 Ontology logic consistency verification successful!")
    else:
        print("🎯 Test result: ❌ Fail")
        print("⚠️ Ontology logic inconsistency found, need to fix")
        sys.exit(1)

if __name__ == "__main__":
    main()
