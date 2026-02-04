#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command line argument parsing module
Handles command line arguments for Manchester syntax generation pipeline
"""

import argparse
from typing import Any


def parse_arguments() -> Any:
    """
    Parse command line arguments
    
    Returns:
        Parsed argument object
    """
    parser = argparse.ArgumentParser(
        description="Manchester syntax generation pipeline - Multi-step execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python test.py --step 1                   # Execute only LLM generation step
  python test.py --step 2                   # Validate latest JSON file
  python test.py --step 2 --file file.json # Validate specified JSON file
  python test.py --step 3                   # Execute hierarchy structure analysis
  python test.py --step all                 # Execute complete pipeline
  python test.py --step list                # List saved files
        """
    )
    
    # Main parameters
    parser.add_argument('--step', type=str, choices=['1', '2', '3', '4', 'all', 'list'], 
                        help='Execution step: 1=Generate Manchester syntax, 2=Vector validation, 3=Hierarchy analysis, 4=Ontology writing, all=Execute all steps, list=List available steps')
    
    parser.add_argument('--file', type=str, 
                       help='Specify JSON file path (used in Step2)')
    
    # Optional parameters
    parser.add_argument('--input', '-i', type=str, 
                       default="Store sharp utensils like kitchen shears and knives safely to prevent harm.",
                       help='Input hazard description text (uses test text by default)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output mode')
    
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Debug mode: show detailed vector similarity matching information, thresholds and matching process')
    
    return parser.parse_args()


def print_step_results(step_name: str, validation_report: dict = None):
    """
    Print step execution results
    
    Args:
        step_name: Step name ('step1', 'step2', 'all')
        validation_report: Validation report (used in Step2 and complete pipeline)
    """
    if step_name == 'step1':
        print(f"\n✅ Step 1 execution completed")
        
    elif step_name == 'step2' and validation_report:
        summary = validation_report.get('summary', {})
        print(f"\n📊 Step 2 validation results summary:")
        print(f"   - Total items checked: {summary.get('total_items', 0)}")
        print(f"   - Existing items: {summary.get('existing_items', 0)}")
        print(f"   - Missing items: {summary.get('missing_items', 0)}")
        print(f"   - Needs review: {'Yes' if summary.get('needs_review', False) else 'No'}")
        
    elif step_name == 'all' and validation_report:
        summary = validation_report.get('summary', {})
        print(f"\n✅ Complete pipeline executed successfully!")
        print(f"\n📊 Final validation results:")
        print(f"   - Coverage ratio: {summary.get('coverage_ratio', 0.0):.1%}")
        print(f"   - Needs review: {'Yes' if summary.get('needs_review', False) else 'No'}")


def print_header():
    """Print program header information"""
    print("🎯 Manchester Syntax Generation Pipeline - Multi-step Execution")
    print("=" * 80)


if __name__ == "__main__":
    # Test CLI parsing
    args = parse_arguments()
    print(f"Parsed arguments: {vars(args)}")
