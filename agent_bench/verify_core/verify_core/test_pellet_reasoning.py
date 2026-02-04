#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pellet reasoner consistency test script
Specifically used to test ontology reasoning consistency
"""

import sys
import os
from pathlib import Path

# Add project root path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_ontology_consistency():
    """Test ontology consistency"""
    try:
        print("🔍 Starting ontology reasoning consistency test")
        print("=" * 60)
        
        # Import dependencies
        try:
            import owlready2 as owl
            from owlready2 import sync_reasoner_pellet
            from .src.ontology_loader import OntologyLoader
        except ImportError as e:
            print(f"❌ Dependency import failed: {e}")
            print("Please ensure owlready2 and Java are installed")
            return "false"
        
        # Initialize ontology loader
        print("📦 Initializing ontology loader...")
        loader = OntologyLoader()
        
        # Display available ontologies
        loader.list_available_ontologies()
        
        # Load all ontologies
        print("\n🌐 Loading all ontologies to World...")
        world, main_onto = loader.load_all_ontologies()
        
        if not world:
            print("❌ Ontology loading failed")
            return "false"
            
        print(f"\n✅ Ontology loading completed")
        print(f"📊 Number of ontologies loaded: {len(list(world.ontologies))}")
        print(f"🎯 Main ontology: {main_onto.base_iri if main_onto else 'None'}")
        
        # Run Pellet reasoner
        print("\n🤖 Starting Pellet reasoner for consistency check...")
        print("⏳ This may take some time, please wait...")
        
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
            print(f"   🏷️  Number of classes: {total_classes}")
            print(f"   🔗 Number of properties: {total_properties}")
            print(f"   👤 Number of individuals: {total_individuals}")
            
            return "success"
            
        except Exception as reasoning_error:
            print(f"\n❌ Reasoning detected inconsistency:")
            print(f"🔥 Error details: {reasoning_error}")
            
            # Try to parse error information
            error_str = str(reasoning_error)
            if "Person is not in the definition order" in error_str:
                print("\n💡 Diagnosis suggestions:")
                print("   🔍 Person class definition order error")
                print("   📝 Possible cause: Person class is referenced but not defined correctly")
                print("   🛠️ Solution: Check the definition of Person class in object.owl")
            elif "InternalReasonerException" in error_str:
                print("\n💡 Diagnosis suggestions:")
                print("   🔍 Internal reasoner exception")
                print("   📝 Possible cause: Ontology structure or class hierarchy definition error")
                print("   🛠️ Solution: Check class inheritance relationships and definition integrity")
                
            return "false"
    
    except Exception as e:
        print(f"\n💥 Test script execution failed: {e}")
        return "false"

def main():
    """Main function"""
    print("🚀 Pellet reasoner consistency test tool")
    print(f"📁 Working directory: {os.getcwd()}")
    
    success = test_ontology_consistency()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 Test result: ✅ Pass")
        print("🎉 Ontology logic consistency verification successful!")
    else:
        print("🎯 Test result: ❌ Fail")
        print("⚠️ Found ontology logic inconsistency, need to fix")
        sys.exit(1)

if __name__ == "__main__":
    main()
