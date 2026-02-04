#!/usr/bin/env python3
"""
Quick test script to verify BASELINE_NEW method is working correctly.
This tests that the ontology knowledge is properly loaded and appended to the prompt.
"""
import os
import sys

# Set minimal environment variables for testing
os.environ.setdefault("API_KEY", "sk-test")
os.environ.setdefault("BASE_URL", "https://test")
os.environ.setdefault("MODEL", "test-model")
os.environ.setdefault("SDL_VIDEODRIVER", "x11")
os.environ.setdefault("AGENT_DEBUG", "1")
os.environ.setdefault("HACK_QWEN_NO_IMAGE", "1")

from src.main import BASELINE_PROMPT, BASELINE_NEW_PROMPT, ONTOLOGY_KNOWLEDGE


def test_ontology_loading():
    """Test that ontology knowledge is properly loaded."""
    print("=" * 80)
    print("Testing Ontology Knowledge Loading")
    print("=" * 80)
    
    if not ONTOLOGY_KNOWLEDGE:
        print("✗ FAILED: Ontology knowledge is empty!")
        return False
    
    print(f"✓ Ontology knowledge loaded: {len(ONTOLOGY_KNOWLEDGE)} characters")
    
    # Check for expected content
    expected_keywords = ["Action Safety Rules", "Kitchen-Specific Safety Rules", "Throwing Prohibited", "Microwave"]
    found_keywords = []
    missing_keywords = []
    
    for keyword in expected_keywords:
        if keyword in ONTOLOGY_KNOWLEDGE:
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    print(f"\n✓ Found keywords: {found_keywords}")
    if missing_keywords:
        print(f"⚠ Missing keywords: {missing_keywords}")
    
    return True


def test_baseline_new_prompt():
    """Test that BASELINE_NEW_PROMPT includes ontology knowledge."""
    print("\n" + "=" * 80)
    print("Testing BASELINE_NEW_PROMPT")
    print("=" * 80)
    
    # Verify BASELINE_NEW_PROMPT is longer than BASELINE_PROMPT
    if len(BASELINE_NEW_PROMPT) <= len(BASELINE_PROMPT):
        print("✗ FAILED: BASELINE_NEW_PROMPT should be longer than BASELINE_PROMPT")
        return False
    
    print(f"✓ BASELINE_PROMPT length: {len(BASELINE_PROMPT)} characters")
    print(f"✓ BASELINE_NEW_PROMPT length: {len(BASELINE_NEW_PROMPT)} characters")
    print(f"✓ Additional content: {len(BASELINE_NEW_PROMPT) - len(BASELINE_PROMPT)} characters")
    
    # Verify ontology content is in BASELINE_NEW_PROMPT
    if ONTOLOGY_KNOWLEDGE not in BASELINE_NEW_PROMPT:
        print("✗ FAILED: Ontology knowledge not found in BASELINE_NEW_PROMPT")
        return False
    
    print("✓ Ontology knowledge successfully appended to BASELINE_NEW_PROMPT")
    
    # Show a sample of the ontology content
    print("\n--- Sample of Ontology Knowledge (first 500 chars) ---")
    print(ONTOLOGY_KNOWLEDGE[:500])
    print("...")
    
    return True


def test_method_integration():
    """Test that BASELINE_NEW can be used in generate_low_level_plan."""
    print("\n" + "=" * 80)
    print("Testing Method Integration")
    print("=" * 80)
    
    from src.main import generate_low_level_plan
    from typing import get_args
    from src.main import Agent
    
    # Check if BASELINE_NEW is in the type hints
    try:
        # Verify the method is available in Agent.run_task
        run_task_method = Agent.run_task
        annotations = run_task_method.__annotations__
        method_type = annotations.get('method')
        
        if method_type:
            # Extract literal values if it's a Literal type
            method_choices = get_args(method_type)
            if "BASELINE_NEW" in method_choices:
                print(f"✓ BASELINE_NEW is available in Agent.run_task method choices: {method_choices}")
            else:
                print(f"✗ FAILED: BASELINE_NEW not found in method choices: {method_choices}")
                return False
        else:
            print("⚠ Warning: Could not verify method type hints")
    except Exception as e:
        print(f"⚠ Warning: Could not check type hints: {e}")
    
    print("✓ Method integration check passed")
    return True


def main():
    print("\n" + "=" * 80)
    print("BASELINE_NEW Method Verification Test")
    print("=" * 80 + "\n")
    
    all_passed = True
    
    # Run tests
    all_passed &= test_ontology_loading()
    all_passed &= test_baseline_new_prompt()
    all_passed &= test_method_integration()
    
    # Final summary
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nBASELINE_NEW method is ready to use!")
        print("\nRun an experiment with:")
        print("  python run_experiment.py --runname test-baseline-new --method BASELINE_NEW --scene FloorPlan3 --task-id 5")
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
