#!/usr/bin/env python3
"""
Batch runner for multiple experiments.
Configure experiments in a JSON file or run all methods.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict


def load_config(config_path: str) -> List[Dict]:
    """Load experiment configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def run_command(cmd: List[str]) -> bool:
    """
    Run a command and return whether it succeeded.
    
    Args:
        cmd: Command to run as list of strings
        
    Returns:
        True if command succeeded, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Command failed with return code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)


def run_batch_from_config(config_path: str):
    """Run batch experiments from configuration file."""
    print(f"Loading configuration from {config_path}...")
    experiments = load_config(config_path)
    
    total = len(experiments)
    succeeded = 0
    failed = 0
    
    for i, exp in enumerate(experiments, 1):
        print(f"\n{'#'*80}")
        print(f"# Experiment {i}/{total}")
        print(f"{'#'*80}")
        
        # Build command
        cmd = ["python", "run_experiment.py"]
        
        # Required arguments
        cmd.extend(["--runname", exp["runname"]])
        cmd.extend(["--method", exp["method"]])
        
        # Optional arguments
        if "scene" in exp:
            cmd.extend(["--scene", exp["scene"]])
        if "task_id" in exp:
            cmd.extend(["--task-id", str(exp["task_id"])])
        if "data_path" in exp:
            cmd.extend(["--data-path", exp["data_path"]])
        if "api_key" in exp:
            cmd.extend(["--api-key", exp["api_key"]])
        if "base_url" in exp:
            cmd.extend(["--base-url", exp["base_url"]])
        if "model" in exp:
            cmd.extend(["--model", exp["model"]])
        
        # Run the experiment
        if run_command(cmd):
            succeeded += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'#'*80}")
    print(f"# Batch Summary")
    print(f"{'#'*80}")
    print(f"Total experiments: {total}")
    print(f"✓ Succeeded: {succeeded}")
    print(f"✗ Failed: {failed}")


def run_all_methods(runname_prefix: str, scene: str = None, task_id: int = None):
    """Run experiments with all available methods."""
    methods = ["BASELINE", "COT", "BASELINE_FEEDBACK", "BASELINE_NEW", "VIRF_SAFETY"]
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    total = len(methods)
    succeeded = 0
    failed = 0
    
    for i, method in enumerate(methods, 1):
        print(f"\n{'#'*80}")
        print(f"# Running method {i}/{total}: {method}")
        print(f"{'#'*80}")
        
        # Create runname with timestamp and method
        runname = f"{runname_prefix}-{method}-{timestamp}"
        
        # Build command
        cmd = [
            "python", "run_experiment.py",
            "--runname", runname,
            "--method", method
        ]
        
        if scene:
            cmd.extend(["--scene", scene])
        if task_id is not None:
            cmd.extend(["--task-id", str(task_id)])
        
        # Run the experiment
        if run_command(cmd):
            succeeded += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'#'*80}")
    print(f"# Batch Summary")
    print(f"{'#'*80}")
    print(f"Total methods: {total}")
    print(f"✓ Succeeded: {succeeded}")
    print(f"✗ Failed: {failed}")


def create_sample_config(output_path: str):
    """Create a sample configuration file."""
    sample_config = [
        {
            "runname": "baseline-test",
            "method": "BASELINE",
            "scene": "FloorPlan3",
            "task_id": 5
        },
        {
            "runname": "baseline-new-test",
            "method": "BASELINE_NEW",
            "scene": "FloorPlan3",
            "task_id": 5
        },
        {
            "runname": "cot-full",
            "method": "COT"
        },
        {
            "runname": "virf-safety-full",
            "method": "VIRF_SAFETY"
        }
    ]
    
    with open(output_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"Sample configuration saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch runner for agent experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all methods with a common prefix
  python run_batch_experiments.py --all-methods --runname-prefix experiment-2025
  
  # Run all methods on a specific scene
  python run_batch_experiments.py --all-methods --runname-prefix test --scene FloorPlan3
  
  # Run experiments from a configuration file
  python run_batch_experiments.py --config experiments.json
  
  # Create a sample configuration file
  python run_batch_experiments.py --create-sample-config sample_config.json
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON configuration file with experiment definitions"
    )
    
    parser.add_argument(
        "--all-methods",
        action="store_true",
        help="Run experiments with all available methods"
    )
    
    parser.add_argument(
        "--runname-prefix",
        type=str,
        default="experiment",
        help="Prefix for run names when using --all-methods (default: experiment)"
    )
    
    parser.add_argument(
        "--scene",
        type=str,
        help="Optional: Filter to specific scene when using --all-methods"
    )
    
    parser.add_argument(
        "--task-id",
        type=int,
        help="Optional: Filter to specific task ID when using --all-methods"
    )
    
    parser.add_argument(
        "--create-sample-config",
        type=str,
        metavar="OUTPUT_PATH",
        help="Create a sample configuration file and exit"
    )
    
    args = parser.parse_args()
    
    # Handle sample config creation
    if args.create_sample_config:
        create_sample_config(args.create_sample_config)
        return
    
    # Validate arguments
    if not args.config and not args.all_methods:
        parser.error("Either --config or --all-methods must be specified")
    
    if args.config and args.all_methods:
        parser.error("Cannot specify both --config and --all-methods")
    
    # Run batch experiments
    if args.config:
        if not Path(args.config).exists():
            print(f"✗ Error: Configuration file not found: {args.config}")
            sys.exit(1)
        run_batch_from_config(args.config)
    else:
        run_all_methods(
            runname_prefix=args.runname_prefix,
            scene=args.scene,
            task_id=args.task_id
        )


if __name__ == "__main__":
    main()
