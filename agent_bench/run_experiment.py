#!/usr/bin/env python3
"""
Launcher script for running agent experiments.
Usage:
    python run_experiment.py --runname VIRF-2025-09-20 --method VIRF_SAFETY
    python run_experiment.py --runname baseline-test --method BASELINE --scene FloorPlan3
    python run_experiment.py --runname test --method COT --scene FloorPlan3 --task-id 5
    python run_experiment.py --runname cot-new-test --method COT_NEW
    python run_experiment.py --runname baseline-new-test --method BASELINE_NEW
"""
import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Literal, Optional


def setup_environment(api_key: Optional[str] = None, 
                      base_url: Optional[str] = None, 
                      model: Optional[str] = None):
    """Setup environment variables for the experiment."""
    # Set API credentials
    if api_key:
        os.environ["API_KEY"] = api_key
    elif "API_KEY" not in os.environ:
        os.environ["API_KEY"] = "sk-XXXXX"
    
    if base_url:
        os.environ["BASE_URL"] = base_url
    elif "BASE_URL" not in os.environ:
        os.environ["BASE_URL"] = "https://XXXX"
    
    if model:
        os.environ["MODEL"] = model
    elif "MODEL" not in os.environ:
        os.environ["MODEL"] = "XXXX"
    
    # Set other required environment variables
    os.environ.setdefault("SDL_VIDEODRIVER", "x11")
    os.environ.setdefault("AGENT_DEBUG", "1")
    os.environ.setdefault("HACK_QWEN_NO_IMAGE", "1")


def load_dataset(data_path: str = "data/organized_by_scene_classified.json"):
    """Load the dataset from JSON file."""
    with open(data_path, "r") as f:
        return json.load(f)


def run_experiment(
    runname: str,
    method: Literal["BASELINE", "COT", "COT_NEW", "BASELINE_FEEDBACK", "BASELINE_NEW", "VIRF_SAFETY"],
    dataset: dict,
    scene_filter: Optional[str] = None,
    task_id_filter: Optional[int] = None,
):
    """
    Run the experiment with specified parameters.
    
    Args:
        runname: Name for this experimental run
        method: The method to use for running tasks
        dataset: The loaded dataset
        scene_filter: If specified, only run tasks in this scene
        task_id_filter: If specified, only run this specific task ID
    """
    from src.main import Agent, ndarray_to_base64
    
    dst = Path(f"results/{runname}.json")
    dst.parent.mkdir(exist_ok=True, parents=True)
    
    # Load existing results if available (with error handling for corrupted files)
    run_results = {}
    if dst.exists():
        try:
            run_results = json.loads(dst.read_text())
            run_results = {f"{r['scene']}_{r['task']['id']}": r for r in run_results}
            print(f"✓ Loaded {len(run_results)} existing results from {dst}")
        except json.JSONDecodeError as e:
            print(f"⚠ Warning: Existing results file is corrupted (JSON error: {e})")
            print(f"⚠ Creating backup and starting fresh...")
            # Backup corrupted file
            backup_path = dst.with_suffix(f".corrupted.{int(time.time())}.json")
            dst.rename(backup_path)
            print(f"⚠ Corrupted file backed up to: {backup_path}")
            run_results = {}

    total_tasks = 0
    completed_tasks = 0
    
    # Iterate through dataset
    for scene, data in dataset.items():
        # Apply scene filter if specified
        if scene_filter and scene != scene_filter:
            continue
            
        for i, d in enumerate(data):
            # Apply task ID filter if specified
            if task_id_filter is not None and i != task_id_filter:
                continue
            
            total_tasks += 1
            task_key = f"{scene}_{i}"
            
            if task_key in run_results:
                print(f"✓ Skipping {scene} task {i} (already completed)")
                completed_tasks += 1
                continue
                
            print(f"\n{'='*80}")
            print(f"Scene: {scene}, Task {i}/{len(data)-1}")
            print(f"Instruction: {d['instruction']}")
            print(f"Method: {method}")
            print(f"{'='*80}\n")
            
            try:
                agent = Agent(scene, d)
                res = agent.run_task(method)
                run_results[task_key] = {
                    "results": res.model_dump(),
                    "scene": scene,
                    "task": d,
                    "last_frame": ndarray_to_base64(agent.controller.last_event.frame)  # type: ignore
                }
                completed_tasks += 1
                print(f"✓ Task completed successfully")
                
            except Exception as e:
                print(f"✗ Error running task {scene} {i}: {e}")
                import traceback
                traceback.print_exc()
                # Optionally store error information
                run_results[task_key] = {
                    "results": {"error": str(e)},
                    "scene": scene,
                    "task": d,
                }
            
            # Save results after each task
            with dst.open("w") as f:
                json.dump(list(run_results.values()), f, indent=2)
            print(f"Results saved to {dst}")
    
    print(f"\n{'='*80}")
    print(f"Experiment completed: {completed_tasks}/{total_tasks} tasks")
    print(f"Results saved to: {dst}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run agent experiments with various methods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full experiment with VIRF_SAFETY method
  python run_experiment.py --runname VIRF-2025-09-20 --method VIRF_SAFETY
  
  # Run only on FloorPlan3 with COT method
  python run_experiment.py --runname cot-floorplan3 --method COT --scene FloorPlan3
  
  # Run a single task for testing
  python run_experiment.py --runname test --method BASELINE --scene FloorPlan3 --task-id 5
  
  # Specify custom API credentials
  python run_experiment.py --runname test --method COT --api-key sk-xxx --base-url https://api.example.com
        """
    )
    
    parser.add_argument(
        "--runname",
        type=str,
        required=True,
        help="Name for this experimental run (used for output filename)"
    )
    
    parser.add_argument(
        "--method",
        type=str,
        required=True,
        choices=["BASELINE", "COT", "COT_NEW", "BASELINE_FEEDBACK", "BASELINE_NEW", "VIRF_SAFETY"],
        help="Method to use for running tasks"
    )
    
    parser.add_argument(
        "--scene",
        type=str,
        default=None,
        help="Optional: Filter to only run tasks in this scene (e.g., FloorPlan3)"
    )
    
    parser.add_argument(
        "--task-id",
        type=int,
        default=None,
        help="Optional: Filter to only run this specific task ID"
    )
    
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/organized_by_scene_classified.json",
        help="Path to dataset JSON file (default: data/organized_by_scene_classified.json)"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for the model (defaults to environment variable or placeholder)"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Base URL for API (defaults to environment variable or placeholder)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to use (defaults to environment variable or placeholder)"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    print("Setting up environment...")
    setup_environment(
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model
    )
    
    # Load dataset
    print(f"Loading dataset from {args.data_path}...")
    try:
        dataset = load_dataset(args.data_path)
        print(f"✓ Loaded dataset with {len(dataset)} scenes")
    except FileNotFoundError:
        print(f"✗ Error: Dataset file not found: {args.data_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON in dataset file: {args.data_path}")
        sys.exit(1)
    
    # Run experiment
    print(f"\nStarting experiment: {args.runname}")
    print(f"Method: {args.method}")
    if args.scene:
        print(f"Scene filter: {args.scene}")
    if args.task_id is not None:
        print(f"Task ID filter: {args.task_id}")
    print()
    
    run_experiment(
        runname=args.runname,
        method=args.method,
        dataset=dataset,
        scene_filter=args.scene,
        task_id_filter=args.task_id,
    )


if __name__ == "__main__":
    main()
