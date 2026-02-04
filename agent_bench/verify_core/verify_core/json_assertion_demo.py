#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-step World State Verifier Demo Script
Mimics the flow of action_sequence_processor.py, but only handles single-step world state setup and safety verification, without action sequences
"""

import sys
import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Add src directory to Python path
sys.path.append('src')

# Import core modules
from .src.abox_tbox_mapper import create_mapper_with_all_ontologies


def load_json_from_file(file_path):
    """
    Load JSON data from file
    
    Args:
        file_path: JSON file path
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None


class SingleStepWorldVerifier:
    """
    Single-step World State Verifier
    Mimics the flow of action_sequence_processor, but only handles single-step world state setup and safety verification
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.mapper = None
        self.safety_verifier = None
        
    def initialize(self):
        """
        Initialize mapper and safety verifier
        """
        print("🔧 Initializing single-step world state verifier...")
        
        # Create mapper and load all ontologies
        self.mapper = create_mapper_with_all_ontologies(verbose=self.verbose)
        if not self.mapper:
            raise Exception("❌ Mapper initialization failed")
            
        # Create safety verifier
        from verify.safety_verifier import SafetyVerifier
        self.safety_verifier = SafetyVerifier(
            external_world=self.mapper.world,
            external_onto=self.mapper.main_ontology,
            verbose=self.verbose
        )
        
        print("✅ Initialization completed")
        
    def process_world_state(self, world_state_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process world state data and perform safety verification
        
        Args:
            world_state_data: Dictionary containing world state information
            
        Returns:
            Dictionary containing safety verification results
        """
        print("\n📍 Starting world state processing...")
        
        try:
            # Step 1: Process JSON data and create ontology instances
            print("\n🔄 Step 1: Creating ontology instances")
            mapping_result = self.mapper.process_json_mapping(world_state_data)
            
            if not mapping_result['success']:
                raise Exception(f"JSON mapping processing failed: {mapping_result['errors']}")
            
            instances_created = len(mapping_result['created_instances'])
            print(f"✅ Created {instances_created} instances")
            print(f"✅ Created {len(mapping_result['created_assertions'])} assertions")
            
            # Step 2: Run reasoning
            print("\n🧠 Step 2: Running OWL reasoning...")
            import owlready2 as owl
            owl.sync_reasoner_pellet(self.mapper.world, infer_property_values=True)
            print("✅ Reasoning completed")
            
            # Step 3: Capture current world state
            print("\n📸 Step 3: Capturing world state...")
            from .src.state_world.world_state_manager import WorldStateManager
            world_manager = WorldStateManager(self.mapper.world, verbose=self.verbose)
            current_state = world_manager.capture_world_state()
            print(f"✅ Captured state of {len(current_state.get('individuals_detail', {}))} individuals")
            
            # Step 4: Execute safety verification
            print("\n🛡️ Step 4: Executing safety verification...")
            safety_result = self.safety_verifier.check_safety()
            
            # Organize results (adapt to SafetyVerifier's return format)
            hazards_list = []
            if safety_result.get('hazards'):
                hazards_list = [hazard.get('violated_rule', {}).get('id', 'Unknown hazard') 
                              for hazard in safety_result['hazards']]
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'world_state': current_state,
                'safety_verification': {
                    'is_safe': safety_result.get('is_safe', True),
                    'hazards_detected': hazards_list,
                    'safety_rules_checked': safety_result.get('hazard_count', 0),
                    'detailed_results': safety_result.get('hazards', []),
                    'message': safety_result.get('message', '')
                },
                'processing_summary': {
                    'instances_created': instances_created,
                    'individuals_captured': len(current_state.get('individuals_detail', {})),
                    'reasoning_completed': True
                }
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error occurred while processing world state: {e}")
            import traceback
            traceback.print_exc()
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'processing_summary': {
                    'instances_created': 0,
                    'individuals_captured': 0,
                    'reasoning_completed': False
                }
            }
    
    def print_safety_summary(self, result: Dict[str, Any]):
        """
        Print safety verification summary
        """
        print("\n" + "="*60)
        print("🛡️ Safety Verification Results Summary")
        print("="*60)
        
        if 'error' in result:
            print(f"❌ Processing failed: {result['error']}")
            return
            
        safety = result.get('safety_verification', {})
        processing = result.get('processing_summary', {})
        
        print(f"📊 Processing Statistics:")
        print(f"   • Instances created: {processing.get('instances_created', 0)}")
        print(f"   • Individuals captured: {processing.get('individuals_captured', 0)}")
        print(f"   • Reasoning completed: {'✅' if processing.get('reasoning_completed') else '❌'}")
        
        print(f"\n🛡️ Safety status: {'✅ Safe' if safety.get('is_safe', True) else '⚠️ Risks detected'}")
        print(f"🔍 Safety rules checked: {safety.get('safety_rules_checked', 0)}")
        
        hazards = safety.get('hazards_detected', [])
        if hazards:
            print(f"⚠️ Detected {len(hazards)} safety hazards:")
            for i, hazard in enumerate(hazards, 1):
                print(f"   {i}. {hazard}")
        else:
            print("✅ No safety hazards detected")
            
        detailed_results = safety.get('detailed_results', [])
        if detailed_results and self.verbose:
            print(f"\n📋 Detailed verification results:")
            for result_item in detailed_results:
                status = "✅" if result_item.get('passed', True) else "❌"
                print(f"   {status} {result_item.get('rule', 'Unknown rule')}")
                if not result_item.get('passed', True) and result_item.get('details'):
                    print(f"      Details: {result_item['details']}")


def main():
    """
    Main function
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Single-step World State Verifier Demo Script')
    parser.add_argument('--input', '--file', type=str, help='JSON input file path')
    parser.add_argument('json_file', nargs='?', help='JSON input file path (positional argument)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output mode')
    parser.add_argument('--output', '-o', type=str, help='Output results to JSON file')
    
    args = parser.parse_args()
    
    # Determine JSON file path
    json_file_path = args.input or args.json_file
    if not json_file_path:
        print("❌ Please provide JSON file path")
        print("Usage: python json_assertion_demo.py <json_file> [--verbose] [--output <output_file>]")
        print("Or: python json_assertion_demo.py --input <json_file> [--verbose] [--output <output_file>]")
        sys.exit(1)
    
    verbose = args.verbose
    output_file = args.output
    
    print("🚀 Starting Single-step World State Verifier")
    print(f"📄 Input file: {json_file_path}")
    print(f"🔧 Verbose mode: {'On' if verbose else 'Off'}")
    if output_file:
        print(f"📤 Output file: {output_file}")
    print("-" * 60)
    
    # Load JSON data
    json_data = load_json_from_file(json_file_path)
    if json_data is None:
        sys.exit(1)
    
    print(f"✅ Successfully loaded JSON data")
    if verbose:
        print(f"📊 Data content preview: {json.dumps(json_data, ensure_ascii=False, indent=2)[:300]}...")
    
    try:
        # Create and initialize verifier
        verifier = SingleStepWorldVerifier(verbose=verbose)
        verifier.initialize()
        
        # Process world state and execute safety verification
        result = verifier.process_world_state(json_data)
        
        # Print result summary
        verifier.print_safety_summary(result)
        
        # If output file is specified, save complete results
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Complete results saved to: {output_file}")
            except Exception as e:
                print(f"❌ Failed to save output file: {e}")
        
        # Set exit code based on safety verification results
        if 'error' in result:
            print("\n❌ Processing failed")
            sys.exit(1)
        elif not result.get('safety_verification', {}).get('is_safe', True):
            print("\n⚠️ Safety hazards detected")
            sys.exit(2)
        else:
            print("\n🎉 World state verification completed, system is safe!")
            sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error occurred during execution: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# For compatibility, create JSONAssertionDemo class as an alias for SingleStepWorldVerifier
class JSONAssertionDemo(SingleStepWorldVerifier):
    """
    JSON Assertion Demo Class
    Inherits from SingleStepWorldVerifier, providing compatible interface
    """
    pass


if __name__ == "__main__":
    main()
