"""
Action Sequence Processor - Main File
Only responsible for JSON processing and world state initialization, action sequence processing is delegated to src/state_world module
"""

import json
import sys
import argparse
import os
from datetime import datetime
from typing import Dict, List, Any

# Import modules
from .src.abox_tbox_mapper import create_mapper_with_all_ontologies


class OutputLogger:
    """Output logger - writes all print output to txt file simultaneously"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.original_stdout = sys.stdout
        
        # Ensure log file directory exists
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Create log file and write start time
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Action Sequence Processing Log ===\n")
            f.write(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")
    
    def write(self, text):
        """Write to console and file simultaneously"""
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
        """Close logger"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{'='*60}\n")
            f.write(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=== Log End ===\n")


class MainActionSequenceProcessor:
    """Main Action Sequence Processor - Only responsible for JSON processing and world initialization"""
    
    def __init__(self, verbose: bool = False):
        """Initialize processor"""
        self.mapper = None
        self.world = None
        self.verbose = verbose
        
    def initialize_world(self) -> bool:
        """Initialize world and ontologies"""
        try:
            if self.verbose:
                print("🌍 Initializing world and ontologies...")
            
            # Use ABoxTBoxMapper to load all ontologies
            self.mapper = create_mapper_with_all_ontologies(verbose=self.verbose)
            self.world = self.mapper.world
            
            if not self.world:
                print("❌ Unable to load ontology files")
                return False
            
            # Create default robot
            self._create_default_robot()
            
            if self.verbose:
                print("✅ World initialization completed")
            return True
            
        except Exception as e:
            print(f"❌ World initialization failed: {e}")
            return False
    
    def _create_default_robot(self):
        """Create default robot my_robot"""
        try:
            if self.verbose:
                print("🤖 Creating default robot...")
            
            # Find Robot class
            robot_class = self.world.search_one(iri="*Robot")
            if not robot_class:
                print("❌ Cannot find Robot class")
                return
            
            # Create my_robot instance
            with self.world:
                my_robot = robot_class("my_robot")
                
                # Set initial state: hand is empty
                hand_is_empty_prop = self.world.search_one(iri="*handIsEmpty")
                if hand_is_empty_prop:
                    # handIsEmpty is not a functional property, need to use list format
                    setattr(my_robot, hand_is_empty_prop.python_name, [True])
                    if self.verbose:
                        print(f"   ✅ Set robot initial state: hand is empty")
                else:
                    print(f"   ⚠️ handIsEmpty property not found")
                
                # Add robot to mapper's instance dictionary for future use
                if hasattr(self.mapper, 'created_instances'):
                    self.mapper.created_instances['my_robot'] = my_robot
                
                if self.verbose:
                    print(f"✅ Created default robot: {my_robot}")
                
        except Exception as e:
            print(f"❌ Failed to create default robot: {e}")
            import traceback
            traceback.print_exc()
    
    def load_scenario_from_json(self, json_file_path: str) -> Dict[str, Any]:
        """Load scenario from JSON file"""
        if self.verbose:
            print(f"📁 Loading scenario file: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
        
        # Validate required fields
        required_fields = ['instances', 'assertions']
        for field in required_fields:
            if field not in scenario:
                raise ValueError(f"JSON file missing required field: {field}")
        
        # action_sequence is optional
        if 'action_sequence' not in scenario:
            scenario['action_sequence'] = []
        
        if self.verbose:
            print(f"✅ Scenario loading completed:")
            print(f"   Instance count: {len(scenario['instances'])}")
            print(f"   Assertion count: {len(scenario['assertions'])}")
            print(f"   Action count: {len(scenario['action_sequence'])}")
        
        return scenario
    
    def setup_initial_world_state(self, scenario: Dict[str, Any]) -> bool:
        """Set up initial world state"""
        try:
            if self.verbose:
                print("🏢 Setting up initial world state...")
            
            # Use ABoxTBoxMapper to process JSON data
            json_data = {
                'instances': scenario['instances'],
                'assertions': scenario['assertions']
            }
            
            mapping_result = self.mapper.process_json_mapping(json_data)
            
            if not mapping_result['success']:
                print(f"❌ World state setup failed: {mapping_result['errors']}")
                return False
            
            if self.verbose:
                print(f"✅ Initial world state setup completed")
                print(f"   Created instances: {len(mapping_result['created_instances'])}")
                print(f"   Created assertions: {len(mapping_result['created_assertions'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ World state setup exception: {e}")
            return False
    

    
    def generate_world_state_sequence(self, action_sequence: List[str], enable_reasoning: bool = True, max_workers: int = None):
        """
        Generate world state sequence - delegate to src/state_world module
        Returns independent world state snapshot sequences, supports parallel processing
        
        Args:
            action_sequence: Action sequence
            enable_reasoning: Whether to enable reasoning
            max_workers: Maximum number of threads, None means no limit
        """
        from .src.state_world.world_state_sequence_generator import WorldStateSequenceGenerator
        
        try:
            if self.verbose:
                print(f"🌍 Enabled world state sequence generation mode (multi-threaded)")
                print(f"🔄 Maximum threads: {max_workers if max_workers else 'Unlimited'}")
            
            # Create world state sequence generator, pass ontology reference and multi-threading configuration
            sequence_generator = WorldStateSequenceGenerator(
                self.world, 
                main_ontology=self.mapper.main_ontology,  # Pass saved ontology reference
                verbose=self.verbose,
                max_workers=max_workers  # Pass multi-threading parameter
            )
            
            # Generate state sequence
            state_sequence = sequence_generator.generate_sequence(
                action_sequence, 
                enable_reasoning=enable_reasoning
            )
            
            return state_sequence
            
        except Exception as e:
            print(f"❌ World state sequence generation failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_safety_report(self, state_sequence, plan_id: str = "default_plan") -> Dict[str, Any]:
        """
        Generate standardized safety report
        
        Args:
            state_sequence: World state sequence
            plan_id: Plan ID
        
        Returns:
            Standardized safety report
        """
        from .verify.sequence_safety_verifier import SequenceSafetyVerifier
        
        try:
            # Safety verification always outputs status, not controlled by verbose
            print(f"🔍 Generating standardized safety report...")
            
            # Create sequence safety verifier
            verifier = SequenceSafetyVerifier(self.world, verbose=self.verbose)
            
            # Debug: Print state sequence information
            print(f"🔍 Starting safety detection, state sequence length: {len(state_sequence)}")
            for state in state_sequence:
                has_reasoning = hasattr(state, 'reasoning_result') and state.reasoning_result
                has_safety = has_reasoning and 'safety_verification' in state.reasoning_result if has_reasoning else False
                print(f"   Step {state.step_number}: reasoning_result={has_reasoning}, safety_verification={has_safety}")
            
            # Execute safety verification and generate standardized report
            result = verifier.verify_sequence_safety(state_sequence, plan_id)
            
            if result is None or not isinstance(result, tuple) or len(result) != 2:
                if self.verbose:
                    print(f"   ❌ Safety verification return value abnormal: {result}")
                return {
                    "status": "ERROR",
                    "message": "Safety verification return value abnormal",
                    "error": f"Expected tuple, got: {type(result)}"
                }
            
            is_safe, safety_report = result
            
            if self.verbose:
                status = "✅ Safe" if is_safe else "⚠️ Danger detected"
                print(f"   {status}")
                if not is_safe and safety_report:
                    danger_count = len(safety_report.get('dangerous_steps', []))
                    print(f"   Dangerous steps count: {danger_count}")
            
            return safety_report
            
        except Exception as e:
            error_msg = f"Safety report generation failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            # Print detailed exception information
            import traceback
            print(f"   📋 Exception details:")
            traceback.print_exc()
            
            return {
                "status": "ERROR",
                "message": error_msg,
                "error": str(e)
            }
    
    def export_safety_report(self, safety_report: Dict[str, Any], output_file: str):
        """Export safety report to JSON file"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(safety_report, f, ensure_ascii=False, indent=2)
            
            if self.verbose:
                print(f"📋 Safety report exported: {output_file}")
                
        except Exception as e:
            print(f"❌ Failed to export safety report: {e}")
            import traceback
            traceback.print_exc()

    
    # The following methods are used for result display and export
    
    def print_sequence_summary(self, state_sequence) -> None:
        """Print world state sequence summary"""
        if not state_sequence:
            print("⚠️ Empty state sequence")
            return
        
        print(f"\n{'='*60}")
        print(f"🌍 World State Sequence Summary")
        print(f"{'='*60}")
        
        # Statistics
        total_states = len(state_sequence)
        successful_steps = sum(1 for state in state_sequence[1:] if state.success)
        failed_steps = sum(1 for state in state_sequence[1:] if not state.success)
        
        reasoning_enabled_steps = sum(
            1 for state in state_sequence[1:] 
            if state.reasoning_result is not None
        )
        
        total_reasoning_time = sum(
            state.reasoning_result.get('reasoning_time_seconds', 0) 
            for state in state_sequence[1:] 
            if state.reasoning_result
        )
        
        total_new_inferences = sum(
            state.reasoning_result.get('new_inferences', 0) 
            for state in state_sequence[1:] 
            if state.reasoning_result
        )
        
        print(f"📊 Basic Statistics:")
        print(f"   Total states: {total_states} (including initial state)")
        print(f"   Successful steps: {successful_steps}")
        print(f"   Failed steps: {failed_steps}")
        
        print(f"\n🧠 Reasoning Statistics:")
        print(f"   Reasoning steps: {reasoning_enabled_steps}/{len(state_sequence)-1}")
        print(f"   Total reasoning time: {total_reasoning_time:.3f}s")
        print(f"   New reasoning inferences: {total_new_inferences}")
        
        # Brief information for each step
        print(f"\n📋 Step Details:")
        for state in state_sequence:
            status_icon = "✅" if state.success else "❌"
            reasoning_info = ""
            
            if state.reasoning_result:
                reasoning_time = state.reasoning_result.get('reasoning_time_seconds', 0)
                new_inferences = state.reasoning_result.get('new_inferences', 0)
                reasoning_info = f" [🧠 {reasoning_time:.3f}s, +{new_inferences}]"
            
            print(f"   {status_icon} Step {state.step_number}: {state.action_applied}{reasoning_info}")
        
        print(f"{'='*60}")
    
    def export_sequence_report(self, state_sequence, output_file: str) -> None:
        """Export world state sequence report to JSON file"""
        try:
            from .src.state_world.world_state_sequence_generator import WorldStateSequenceGenerator
            
            # Create temporary generator for export
            temp_generator = WorldStateSequenceGenerator(self.world)
            temp_generator.export_sequence_to_json(state_sequence, output_file)
            
            print(f"📊 World state sequence report exported: {output_file}")
            
        except Exception as e:
            print(f"❌ Failed to export world state sequence report: {e}")
            import traceback
            traceback.print_exc()
    



def main():
    """Main function: Demonstrate action sequence processing"""
    
    # --- Argument parsing ---
    parser = argparse.ArgumentParser(description="Action Sequence Processor")
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true', 
        help="Enable verbose log output"
    )
    parser.add_argument(
        '--input', '-i',
        type=str, 
        default="output/test_action_sequence.json",
        help="Specify input scenario JSON file path (relative or absolute path)"
    )
    parser.add_argument(
        '--scenario', 
        type=str, 
        help="[Deprecated] Use --input or -i parameter instead"
    )
    parser.add_argument(
        '--max',
        type=int,
        default=None,
        help="Maximum number of threads, default is None (no thread limit)"
    )
    args = parser.parse_args()
    
    # Create log filename (with timestamp)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join("output", "log", f"action_sequence_log_{timestamp}.txt")
    
    # Create output logger
    logger = OutputLogger(log_filename)
    
    try:
        # Redirect standard output to logger
        sys.stdout = logger
        
        print(f"📝 Log output enabled, file: {log_filename}")
        if args.verbose:
            print(f"🔄 Verbose log mode activated")
        
        # Create main processor
        processor = MainActionSequenceProcessor(verbose=args.verbose)
        
        # Initialize world
        if not processor.initialize_world():
            return
        
        # Determine input file path (prioritize new --input parameter)
        input_file = args.input if args.scenario is None else args.scenario
        if args.scenario is not None:
            print("⚠️  Warning: --scenario parameter is deprecated, please use --input or -i parameter")
        
        print(f"📁 Loading scenario file: {input_file}")
        
        # Load scenario
        scenario = processor.load_scenario_from_json(input_file)
        
        # Set up initial world state
        if not processor.setup_initial_world_state(scenario):
            return
        
        # Generate world state sequence (delegate to src/state_world module)
        state_sequence = processor.generate_world_state_sequence(
            scenario['action_sequence'], 
            enable_reasoning=True,
            max_workers=args.max  # Use thread count specified by command line parameter
        )
        
        # --- Standardized safety verification ---
        
        # Extract plan_id (if exists)
        plan_id = scenario.get('plan_id', 'unknown_plan')
        
        # Generate standardized safety report (using safety verification results from reasoning copies)
        safety_report = processor.generate_safety_report(state_sequence, plan_id)
        
        # --- Result processing ---
        if safety_report is None:
            print("\n❌ Safety report generation failed")
            return
        
        status = safety_report.get('status', 'UNKNOWN')
        
        if status == 'SAFE':
            print("\n✅ Sequence safety verification passed")
        elif status == 'WARNING':
            print("\n⚠️ Warning situation detected")
            # Print warning report to console
            print(json.dumps(safety_report, indent=2, ensure_ascii=False))
        elif status == 'UNSAFE':
            print("\n🚨 Dangerous situation detected")
            # Print danger report to console
            print(json.dumps(safety_report, indent=2, ensure_ascii=False))
        else:
            print(f"\n❓ Unknown status: {status}")
            print(json.dumps(safety_report, indent=2, ensure_ascii=False))
        
        # Export standardized safety report
        safety_report_file = os.path.join("output", "log", f"safety_report_{timestamp}.json")
        processor.export_safety_report(safety_report, safety_report_file)
        
        # Print sequence summary
        processor.print_sequence_summary(state_sequence)
        
        # Export state sequence report
        sequence_report_file = os.path.join("output", "log", f"world_state_sequence_report_{timestamp}.json")
        processor.export_sequence_report(state_sequence, sequence_report_file)
        
        print(f"\n📝 Complete log saved to: {log_filename}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Restore standard output
        sys.stdout = logger.original_stdout
        # Close logger
        logger.close()
        
        print(f"\n📝 Log file saved: {log_filename}")


if __name__ == "__main__":
    main()
