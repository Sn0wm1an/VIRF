#!/usr/bin/env python3
"""
Analysis of task execution failures
Analyze all failed tasks in detail and provide statistics
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter

def load_results_data(results_file: str) -> List[Dict[str, Any]]:
    """Load results data from JSON file"""
    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_execution_failures(results_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze execution failures in detail"""
    
    stats = {
        'total_tasks': len(results_data),
        'executed_tasks': 0,
        'successful_tasks': 0,
        'failed_tasks': 0,
        'no_execution_tasks': 0,
        'failure_details': [],
        'failure_categories': defaultdict(list),
        'failure_by_scene': defaultdict(int),
        'failure_by_action': defaultdict(int),
        'step_failure_analysis': defaultdict(int)
    }
    
    for i, entry in enumerate(results_data):
        scene = entry.get('scene', 'Unknown')
        task = entry.get('task', {})
        results = entry.get('results', {})
        
        task_id = task.get('id')
        instruction = task.get('instruction', 'No instruction')
        category = task.get('category', 'unknown')
        results_list = results.get('results')
        
        # Check if task was executed
        if not results_list or not isinstance(results_list, list) or len(results_list) == 0:
            stats['no_execution_tasks'] += 1
            stats['failure_categories']['no_execution'].append({
                'index': i,
                'scene': scene,
                'task_id': task_id,
                'instruction': instruction,
                'category': category,
                'reason': 'No execution results'
            })
            continue
            
        stats['executed_tasks'] += 1
        
        # Check execution success
        all_steps_success = all(r.get("success", False) for r in results_list)
        
        if all_steps_success:
            stats['successful_tasks'] += 1
        else:
            stats['failed_tasks'] += 1
            stats['failure_by_scene'][scene] += 1
            
            # Analyze failure details
            failed_steps = []
            for step_idx, step in enumerate(results_list):
                if not step.get("success", False):
                    action = step.get('action', 'unknown_action')
                    action_type = action.split(' ')[0] if action else 'unknown'
                    
                    failed_steps.append({
                        'step_index': step_idx,
                        'action': action,
                        'action_type': action_type,
                        'error': step.get('error', 'No error info')
                    })
                    
                    stats['failure_by_action'][action_type] += 1
                    stats['step_failure_analysis'][f'step_{step_idx}'] += 1
            
            # Categorize failure type
            failure_type = categorize_failure_type(results_list, failed_steps)
            
            failure_detail = {
                'index': i,
                'scene': scene,
                'task_id': task_id,
                'instruction': instruction,
                'category': category,
                'failure_type': failure_type,
                'total_steps': len(results_list),
                'failed_steps_count': len(failed_steps),
                'failed_steps': failed_steps,
                'execution_sequence': [r.get('action', '') for r in results_list],
                'success_sequence': [r.get('success', False) for r in results_list]
            }
            
            stats['failure_details'].append(failure_detail)
            stats['failure_categories'][failure_type].append(failure_detail)
    
    return stats

def categorize_failure_type(results_list: List[Dict], failed_steps: List[Dict]) -> str:
    """Categorize the type of failure based on failure patterns"""
    
    if not failed_steps:
        return 'unknown'
    
    total_steps = len(results_list)
    failed_count = len(failed_steps)
    
    # First step failure
    if failed_steps[0]['step_index'] == 0:
        return 'first_step_failure'
    
    # Last step failure
    if failed_steps[-1]['step_index'] == total_steps - 1:
        return 'final_step_failure'
    
    # Middle step failure
    if failed_count == 1:
        return 'single_step_failure'
    
    # Multiple consecutive failures
    if failed_count > 1:
        indices = [step['step_index'] for step in failed_steps]
        if all(indices[i] + 1 == indices[i + 1] for i in range(len(indices) - 1)):
            return 'consecutive_failures'
        else:
            return 'scattered_failures'
    
    # Action-specific failures
    action_types = [step['action_type'] for step in failed_steps]
    if 'find' in action_types:
        return 'find_action_failure'
    elif 'pick' in action_types:
        return 'pick_action_failure'
    elif 'put' in action_types:
        return 'put_action_failure'
    elif 'open' in action_types:
        return 'open_action_failure'
    
    return 'mixed_failures'

def generate_failure_report(stats: Dict[str, Any]) -> str:
    """Generate detailed failure analysis report"""
    
    report = []
    report.append("=" * 80)
    report.append("TASK EXECUTION FAILURE ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Basic statistics
    report.append("📊 BASIC STATISTICS")
    report.append("-" * 40)
    report.append(f"Total tasks: {stats['total_tasks']}")
    report.append(f"Executed tasks: {stats['executed_tasks']}")
    report.append(f"Successful tasks: {stats['successful_tasks']}")
    report.append(f"Failed tasks: {stats['failed_tasks']}")
    report.append(f"No execution tasks: {stats['no_execution_tasks']}")
    
    if stats['executed_tasks'] > 0:
        execution_rate = stats['executed_tasks'] / stats['total_tasks']
        success_rate = stats['successful_tasks'] / stats['executed_tasks']
        failure_rate = stats['failed_tasks'] / stats['executed_tasks']
        
        report.append(f"Execution rate: {execution_rate:.3f} ({stats['executed_tasks']}/{stats['total_tasks']})")
        report.append(f"Success rate: {success_rate:.3f} ({stats['successful_tasks']}/{stats['executed_tasks']})")
        report.append(f"Failure rate: {failure_rate:.3f} ({stats['failed_tasks']}/{stats['executed_tasks']})")
    
    report.append("")
    
    # Failure by scene
    report.append("🏠 FAILURE DISTRIBUTION BY SCENE")
    report.append("-" * 40)
    for scene, count in sorted(stats['failure_by_scene'].items()):
        report.append(f"{scene}: {count} failures")
    report.append("")
    
    # Failure by action type
    report.append("⚡ FAILURE DISTRIBUTION BY ACTION TYPE")
    report.append("-" * 40)
    for action, count in sorted(stats['failure_by_action'].items(), key=lambda x: x[1], reverse=True):
        report.append(f"{action}: {count} failures")
    report.append("")
    
    # Failure categories
    report.append("📋 FAILURE CATEGORIES")
    report.append("-" * 40)
    for category, failures in stats['failure_categories'].items():
        if category != 'no_execution':
            report.append(f"{category}: {len(failures)} cases")
    report.append("")
    
    # Step failure analysis
    report.append("📍 STEP POSITION FAILURE ANALYSIS")
    report.append("-" * 40)
    for step_pos, count in sorted(stats['step_failure_analysis'].items()):
        report.append(f"{step_pos}: {count} failures")
    report.append("")
    
    # Detailed failure examples
    report.append("🔍 DETAILED FAILURE EXAMPLES (Top 10)")
    report.append("-" * 40)
    failure_details = sorted(stats['failure_details'], key=lambda x: x['failed_steps_count'], reverse=True)
    
    for i, failure in enumerate(failure_details[:10]):
        report.append(f"\n{i+1}. Task {failure['task_id']} ({failure['scene']})")
        report.append(f"   Instruction: {failure['instruction']}")
        report.append(f"   Category: {failure['category']}")
        report.append(f"   Failure Type: {failure['failure_type']}")
        report.append(f"   Total Steps: {failure['total_steps']}, Failed: {failure['failed_steps_count']}")
        
        report.append(f"   Execution Sequence:")
        for j, (action, success) in enumerate(zip(failure['execution_sequence'], failure['success_sequence'])):
            status = "✅" if success else "❌"
            report.append(f"     Step {j}: {status} {action}")
        
        if failure['failed_steps']:
            report.append(f"   Failed Steps Details:")
            for step in failure['failed_steps']:
                report.append(f"     Step {step['step_index']}: {step['action']} -> {step['error']}")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """Main function"""
    results_file = "results/BASELINE-2025-09-15.json"
    output_dir = Path("results/")
    
    print("🔍 Starting task execution failure analysis...")
    
    # Load data
    results_data = load_results_data(results_file)
    
    # Analyze failures
    stats = analyze_execution_failures(results_data)
    
    # Generate report
    report = generate_failure_report(stats)
    
    # Save results
    output_file = output_dir / "execution_failure_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
    
    # Save report
    report_file = output_dir / "execution_failure_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Analysis complete!")
    print(f"📄 Detailed results: {output_file}")
    print(f"📋 Report: {report_file}")
    print("")
    
    # Print summary
    print("=" * 60)
    print("EXECUTION FAILURE SUMMARY")
    print("=" * 60)
    
    print(f"Total tasks: {stats['total_tasks']}")
    print(f"Executed tasks: {stats['executed_tasks']}")
    print(f"Failed tasks: {stats['failed_tasks']}")
    
    if stats['executed_tasks'] > 0:
        failure_rate = stats['failed_tasks'] / stats['executed_tasks']
        print(f"Failure rate: {failure_rate:.3f}")
    
    print("\nTop failure types:")
    for category, failures in sorted(stats['failure_categories'].items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        if category != 'no_execution':
            print(f"  {category}: {len(failures)} cases")
    
    print("\nTop failing actions:")
    for action, count in sorted(stats['failure_by_action'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {action}: {count} failures")
    
    print("\n" + "="*60)
    print("REPORT PREVIEW:")
    print("="*60)
    print(report[:2000] + "..." if len(report) > 2000 else report)

if __name__ == "__main__":
    main()
