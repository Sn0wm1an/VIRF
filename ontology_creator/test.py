#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manchester syntax generation pipeline - Main entry file
Step 1: LLM generates Manchester JSON and saves
Step 2: Vector validation of saved JSON

Usage:
  python test.py --step1    # Execute only LLM generation step
  python test.py --step2    # Execute only vector validation step
  python test.py --all      # Execute complete pipeline
"""

import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from pipeline.manchester_pipeline import ManchesterPipeline
    from pipeline.cli_parser import parse_arguments, print_step_results, print_header
    from pipeline.ontology_writer_refactored import write_ontology_from_analysis
    print("✅ Successfully imported test modules")
except ImportError as e:
    print(f"❌ Failed to import test modules: {e}")
    sys.exit(1)




def main():
    """Main function - core execution logic"""
    print_header()
    
    # Parse command line arguments
    print("🔧 Parsing command line arguments...")
    args = parse_arguments()
    print(f"🔧 Parsing completed, parameters: step={args.step}, file={getattr(args, 'file', None)}")
    
    # Initialize pipeline
    pipeline = ManchesterPipeline()
    
    try:
        print("🔧 Starting main logic execution...")
        if args.step == '1':
            # Execute Step 1: LLM generation
            print("\n🎯 Executing Step 1: LLM generating Manchester JSON")
            filepath = pipeline.step1_generate_json(args.input)
            print(f"\n📄 File saved to: {filepath}")
            print_step_results('step1')
            
        elif args.step == '2':
            # Execute Step 2: Vector validation
            print("\n🔍 Executing Step 2: Vector validation")
            if args.file:
                pipeline.step2_validate_json(args.file, debug=args.debug)
            else:
                pipeline.step2_validate_json(debug=args.debug)
            
        elif args.step == '3':
            # Execute Step 3: Hierarchy structure analysis
            print("\n🌳 Executing Step 3: Hierarchy structure analysis")
            if args.file:
                pipeline.step3_analyze_hierarchy(args.file, debug=args.debug)
            else:
                pipeline.step3_analyze_hierarchy(debug=args.debug)
        
        elif args.step == '4':
            # Execute Step 4: Ontology writing
            print("\n📝 Executing Step 4: Ontology writing")
            if args.file:
                result = write_ontology_from_analysis(args.file, debug=args.debug)
            else:
                # Use latest hierarchy analysis file
                result = pipeline.step4_write_ontology(debug=args.debug)
            
            if result['status'] == 'completed':
                print(f"✅ Ontology writing completed!")
                summary = result.get('summary', {})
                print(f"   - Classes written: {summary.get('total_classes_written', 0)}")
                print(f"   - Rules written: {summary.get('total_rules_written', 0)}")
                print(f"   - Files modified: {summary.get('files_modified', 0)}")
                if summary.get('reasoning_passed'):
                    print(f"   - Reasoning validation: ✅ Passed")
                else:
                    print(f"   - Reasoning validation: ⚠️ Skipped or failed")
            else:
                print(f"❌ Ontology writing failed: {result.get('error', 'Unknown error')}")
            
        elif args.step == 'all':
            # Execute complete four-step process
            print("\n🚀 Executing complete four-step process (1→2→3→4)")
            result = pipeline.run_all_steps(args.input)
            if result['success']:
                # Display detailed result summary
                summary = result.get('summary', {})
                print(f"\n✅ All four steps completed!")
                print(f"📊 Execution summary:")
                print(f"   - Total steps: {summary.get('total_steps', 4)}")
                print(f"   - New classes: {summary.get('classes_written', 0)}")
                print(f"   - New rules: {summary.get('rules_written', 0)}")
                print(f"   - Reasoning validation: {'✅ Passed' if summary.get('reasoning_passed') else '⚠️ Skipped'}")
            else:
                print(f"❌ Execution failed: {result['error']}")
                return 1
            
        elif args.step == 'list':
            # List files
            pipeline.list_saved_files()
            
    except Exception as e:
        print(f"❌ Error occurred during execution: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Program interrupted by user")
    except Exception as e:
        print(f"❌ Program execution error: {e}")
        import traceback
        traceback.print_exc()