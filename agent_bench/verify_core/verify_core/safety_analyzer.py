#!/usr/bin/env python3
"""
Safety analysis module
Encapsulates action sequence safety detection functionality, provides standardized API interface
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Import split modules
from .src.input.result_analyzer import ResultAnalyzer
from .src.input.safety_checker import SafetyChecker
from .src.input.scene_analyzer import SceneAnalyzer
from .src.input.input_mapper import ObjectMappingError


class OutputLogger:
    """Output logger - simultaneously write all print output to txt file"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.original_stdout = sys.stdout
        
        # Ensure log file directory exists
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Create log file and write start time
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Safety Analysis Log ===\n")
            f.write(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")
    
    def write(self, text):
        """Write to both console and file simultaneously"""
        # Write to console
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        # Write to file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(text)
            f.flush()
    
    def flush(self):
        """Flush output"""
        self.original_stdout.flush()
    
    def close(self):
        """Close log recorder"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{'='*60}\n")
            f.write(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=== Log End ===\n")


class SafetyAnalyzer:
    """Safety analyzer - unified safety detection interface"""
    
    def __init__(self, verbose: bool = False, max_workers: int = None, ablation_reject: bool = False):
        """
        Initialize safety analyzer
        
        Args:
            verbose: Whether to output detailed logs
            max_workers: Maximum number of threads, None means no limit
            ablation_reject: Whether to enable Ablation mode, uniformly handle UNSAFE and WARNING
        """
        self.verbose = verbose
        self.max_workers = max_workers
        self.ablation_reject = ablation_reject
        self.output_logger = None  # Output log recorder
        
        # Initialize sub-modules
        self.result_analyzer = ResultAnalyzer(verbose=verbose)
        self.safety_checker = SafetyChecker(verbose=verbose, max_workers=max_workers)
        self.scene_analyzer = SceneAnalyzer(verbose=verbose)
    
    def analyze_safety_from_scene(self, floor_plan_name: str, action_sequence: List[str], plan_id: str = None) -> Dict[str, Any]:
        """
        Analyze safety from scene name and action sequence
        
        Args:
            floor_plan_name: Scene name (e.g. "FloorPlan1")
            action_sequence: Action sequence (e.g. ["find apple", "pick apple"])
            plan_id: Optional plan ID
            
        Returns:
            Safety analysis result: {"status": "SAFE"|"WARNING"|"UNSAFE"|"UNKNOWN", "formatted_prompt": str}
        """
        # Start log recording system
        if not plan_id:
            plan_id = f"plan_{datetime.now().strftime('%H%M%S')}"
        
        # Generate log filename: date_sceneName_planID.txt
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"output/log/{timestamp}_{floor_plan_name}_{plan_id}.txt"
        
        # Start output log recorder
        self.output_logger = OutputLogger(log_filename)
        original_stdout = sys.stdout
        sys.stdout = self.output_logger
        
        try:
            print(f"🔍 Starting safety analysis")
            print(f"Scene: {floor_plan_name}")
            print(f"Plan ID: {plan_id}")
            print(f"Action sequence: {action_sequence}")
            print(f"{'='*60}")
            
            # 1. Scene analysis
            scene_result = self.scene_analyzer.analyze_safety_from_scene(floor_plan_name, action_sequence, plan_id)
            
            if scene_result["status"] == "MAPPING_ERROR":
                result = {
                    "status": "UNKNOWN",
                    "formatted_prompt": f"Unable to map objects in action sequence: {scene_result['error']}"
                }
                print(f"⚠️ Scene analysis failed: {scene_result['error']}")
                return result
            elif scene_result["status"] == "ERROR":
                result = {
                    "status": "SAFE", 
                    "formatted_prompt": ""
                }
                print(f"\n⚠️ Scene analysis error, returning safe status")
                return result
            
            # 2. Safety check
            input_data = scene_result["data"]
            print(f"\n🛡️ Performing safety check...")
            result = self.analyze_safety(input_data)
            
            print(f"\n📊 Analyzing check results...")
            print(f"Status: {result.get('status')}")
            print(f"Prompt length: {len(result.get('formatted_prompt', ''))}")
            
            return result
            
        finally:
            # Restore original output and close log recorder
            sys.stdout = original_stdout
            if self.output_logger:
                self.output_logger.close()
                self.output_logger = None
    
    def analyze_safety(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze safety of action sequence
        
        Args:
            input_data: Input data containing instances, assertions and action sequence
            
        Returns:
            Safety analysis result
        """
        try:
            # 1. Input data validity verification
            is_valid, validation_errors = self.safety_checker.check_input_data_validity(input_data)
            if not is_valid:
                if self.verbose:
                    print(f"[SafetyAnalyzer] Input data verification failed: {validation_errors}")
                return {
                    "status": "SAFE",
                    "formatted_prompt": ""
                }
            
            # 2. Run safety check
            results, error_messages = self.safety_checker.run_safety_check_from_data(input_data)
            
            # 3. Analyze results
            analysis_result = self.result_analyzer.analyze_results_robust(results, error_messages)
            
            # 5. Ablation mode handling
            if self.ablation_reject and analysis_result.get("status") in ["UNSAFE", "WARNING"]:
                print(f"🚨 Ablation mode: adjusting {analysis_result.get('status')} to UNSAFE")
                analysis_result["status"] = "UNSAFE"
                analysis_result["formatted_prompt"] = "This plan has been rejected due to safety concerns."
            
            print(f"✅ Safety analysis completed, status: {analysis_result.get('status', 'UNKNOWN')}")
            
            # 4. Format return (normal mode)
            formatted_prompt = self.result_analyzer.format_safety_prompt(analysis_result)
            
            return {
                "status": analysis_result["status"],
                "formatted_prompt": formatted_prompt
            }
            
        except Exception as e:
            # Final exception handling
            final_error = f"Result analysis error: {str(e)}"
            if self.verbose:
                print(f"[SafetyAnalyzer] Result analysis error: {final_error}")
            
            return {
                "status": "SAFE",
                "formatted_prompt": f"Safety analysis failed: {str(e)}"
            }
    
    def get_available_scenes(self) -> List[str]:
        """
        Get all available scene names
        
        Returns:
            List of scene names
        """
        return self.scene_analyzer.get_available_scenes()
    
    def validate_scene_exists(self, floor_plan_name: str) -> bool:
        """
        Validate whether scene file exists
        
        Args:
            floor_plan_name: Scene name
            
        Returns:
            Whether it exists
        """
        return self.scene_analyzer.validate_scene_exists(floor_plan_name)
    


def analyze_action_sequence_safety(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function: Analyze the safety of action sequences
    
    Args:
        input_data: Input data containing instances, assertions and action sequences
        
    Returns:
        Safety analysis result: {"status": "SAFE"|"WARNING"|"UNSAFE", "formatted_prompt": str}
    """
    try:
        # Create analyzer instance
        analyzer = SafetyAnalyzer(verbose=False)
        
        # Execute analysis
        return analyzer.analyze_safety(input_data)
        
    except Exception as e:
        # Log error but return default SAFE status when error occurs
        error_msg = f"Analysis failed: {str(e)}"
        print(f"[analyze_action_sequence_safety] ERROR: {error_msg}")
        
        return {
            "status": "SAFE",
            "formatted_prompt": ""
        }


# Command line interface function
def analyze_action_sequence_safety_from_file(input_file: str):
    """Read data from JSON file and analyze safety"""
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        print(f"📄 Reading input file: {input_file}")
        print("Input data:", input_data)
        
        # Execute safety analysis
        result = analyze_action_sequence_safety(input_data)
        
        # Output results
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ Safety analysis failed: {str(e)}")
        error_result = {
            "status": "ERROR",
            "error": f"Safety analysis failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


def main():
    """Command line entry function"""
    if len(sys.argv) != 2:
        print("Usage: kitchen-safety <input_json_file>")
        print("Or: python -m verify_core.safety_analyzer <input_json_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    analyze_action_sequence_safety_from_file(input_file)


if __name__ == "__main__":
    main()
