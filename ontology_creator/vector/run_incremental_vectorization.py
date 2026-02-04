#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Incremental vectorization main process script
Coordinate execution: class list generation -> LLM description generation -> vectorization
"""

import os
import sys
import subprocess
from datetime import datetime


def run_command(script_name):
    """Run Python script and return success status"""
    print(f"\n🔧 Running: {script_name}")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Run failed: {e}")
        return False


def main():
    """Main process"""
    print("=" * 60)
    print("🚀 Start incremental vectorization process")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Generate ontology class list (automatically detect new classes)
    print("\n📋 Step 1: Generate ontology class list and detect new classes")
    if not run_command("list_ontology_classes.py"):
        print("❌ Class list generation failed")
        return 1
    
    # Step 2: Generate relation property list (required)
    print("\n📋 Step 2: Generate relation property list and detect new properties")
    if not run_command("list_relation_properties.py"):
        print("⚠️ Relation property list generation failed, continue processing...")
    else:
        print("✅ Relation property list generated successfully")
    
    # Step 3: Generate LLM descriptions for new classes
    print("\n🤖 Step 3: Generate LLM descriptions (only new items)")
    if not run_command("generate_llm_descriptions.py"):
        print("❌ LLM description generation failed")
        return 1
    
    # Step 4: Vectorize based on descriptions
    print("\n📊 Step 4: Vectorize based on descriptions")
    if not run_command("vectorize_from_descriptions.py"):
        print("❌ Vectorization failed")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ Incremental vectorization process completed!")
    print("=" * 60)
    print("\n📁 Output files:")
    print("  - output/vector/ontology_classes.json (Ontology class list)")
    print("  - output/vector/new_classes.json (New class list)")
    print("  - output/vector/ontology_llm_descriptions.json (LLM description)")
    print("  - output/vector/ontology_vectors.json (Vector result)")
    print("  - output/vector/ontology_vectors.pkl (Vector binary)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
