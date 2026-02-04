"""
World state sequence generator - generates independent world state snapshot sequences
Supports parallel reasoning and state rollback, supports multi-threaded parallel processing
"""

import copy
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import owlready2 as owl
import tempfile
import os

from .action_executor import ActionExecutor
from .world_state_manager import WorldStateManager
from .action_semantics import parse_action_sequence
from .reasoning_validator import ReasoningValidator


@dataclass
class WorldStateSnapshot:
    """World state snapshot data class"""
    step_number: int
    action_applied: str
    world_snapshot: Dict[str, Any]
    reasoning_result: Optional[Dict[str, Any]]
    success: bool
    errors: List[str]
    processing_time: float = 0.0  # Processing time for this step (seconds)
    timestamp: str = ""  # Timestamp


class WorldStateSequenceGenerator:
    """World state sequence generator"""
    
    def __init__(self, world, main_ontology=None, verbose: bool = False, max_workers: Optional[int] = None):
        """
        Initialize world state sequence generator
        
        Args:
            world: OWL world instance
            main_ontology: Main ontology (optional)
            verbose: Whether to enable verbose logging
            max_workers: Maximum number of threads, None means no limit (use default)
        """
        self.world = world
        self.main_ontology = main_ontology
        self.verbose = verbose
        self.max_workers = max_workers
        # Track context state
        self.current_held_object = None
        self.last_found_object = None
        self.action_executor = ActionExecutor(world, verbose=verbose)
        self.world_state_manager = WorldStateManager(world, verbose=verbose)
        self.reasoning_validator = ReasoningValidator(verbose=verbose)
        # Thread-safe lock
        self._lock = threading.Lock()
    
    def _process_action_step(self, step_num: int, action_str: str, next_action_str: str = None,
                           current_held_object: str = None, last_found_object: str = None,
                           enable_reasoning: bool = True) -> WorldStateSnapshot:
        """Process single action step (thread-safe)"""
        step_start_time = time.time()
        thread_id = threading.get_ident() % 10000  # Simplified thread ID
        timestamp = time.strftime('%H:%M:%S')
        
        if self.verbose:
            print(f"\n🧵 [{timestamp}|T{thread_id:04d}] === Step {step_num} started ===")
            print(f"🧵 [{timestamp}|T{thread_id:04d}] Action: {action_str}")
            print(f"🧵 [{timestamp}|T{thread_id:04d}] Context: holding={current_held_object}, found={last_found_object}")
        
        try:
            # 🔑 Reconstruct reasoning copy from captured world snapshot (ensure cumulative effects are included)
            step_world = self._create_reasoning_copy_from_snapshot(world_snapshot)
            if not step_world:
                return WorldStateSnapshot(
                    step_number=step_num,
                    action_applied=action_str,
                    world_snapshot={},
                    reasoning_result=None,
                    success=False,
                    errors=[f"World copy creation failed"],
                    processing_time=time.time() - step_start_time,
                    timestamp=time.strftime('%Y%m%d_%H%M%S')
                )
            
            # 🔑 Sync world copy with context state
            self._sync_world_with_context(step_world, current_held_object, last_found_object, step_num)
            
            # 🔑 Apply action to world copy
            action_success, action_errors = self._apply_action_to_world_copy(
                step_world, action_str, step_num
            )
            
            # 🔑 Capture world snapshot after action execution
            clean_world_snapshot = None
            if action_success:
                clean_world_snapshot = self._capture_world_snapshot(step_world)
                if self.verbose:
                    print(f"   📸 [Thread {thread_id}] Step {step_num} captured world snapshot after action execution")
            
            # 🔑 Use ReasoningValidator for reasoning validation
            reasoning_result = None
            has_interrupt_danger = False
            if enable_reasoning and action_success and clean_world_snapshot:
                if self.verbose:
                    if next_action_str:
                        print(f"   🧠 [Thread {thread_id}] Step {step_num} reasoning validation for next action '{next_action_str}'")
                    else:
                        print(f"   🧠 [Thread {thread_id}] Step {step_num} (final step) reasoning validation for current state")
                
                reasoning_result, has_interrupt_danger = self.reasoning_validator.validate_step_safety(
                    world_snapshot=clean_world_snapshot,
                    step_num=step_num,
                    action_str=action_str,
                    next_action_str=next_action_str,
                    current_held_object=current_held_object,
                    last_found_object=last_found_object
                )
                
                if has_interrupt_danger:
                    if self.verbose:
                        print(f"🧵 [{time.strftime('%H:%M:%S')}|T{thread_id:04d}] 🚨 InterruptDangerousSituation detected")
            
            # Create state snapshot
            snapshot = WorldStateSnapshot(
                step_number=step_num,
                action_applied=action_str,
                world_snapshot=clean_world_snapshot if action_success else {},
                reasoning_result=reasoning_result,
                success=action_success,
                errors=action_errors,
                processing_time=time.time() - step_start_time,
                timestamp=time.strftime('%Y%m%d_%H%M%S')
            )
            
            if self.verbose:
                print(f"🧵 [{time.strftime('%H:%M:%S')}|T{thread_id:04d}] ✅ Step {step_num} processed ({time.time() - step_start_time:.2f}s)")
            
            return snapshot
            
        except Exception as e:
            if self.verbose:
                print(f"🧵 [{time.strftime('%H:%M:%S')}|T{thread_id:04d}] ❌ Step {step_num} exception: {e}")
            step_end_time = time.time()
            return WorldStateSnapshot(
                step_number=step_num,
                action_applied=action_str,
                world_snapshot=None,
                reasoning_result=None,
                success=False,
                errors=[f"Action syntax error: {str(e)}"],
                processing_time=step_end_time - step_start_time,
                timestamp=time.strftime('%Y%m%d_%H%M%S')
            )
    
    def generate_sequence(self, action_sequence: List[str], enable_reasoning: bool = True) -> List[WorldStateSnapshot]:
        """
        Generate world state sequence - supports multi-threaded parallel processing
        
        Args:
            action_sequence: Action sequence
            enable_reasoning: Whether to enable reasoning
            
        Returns:
            World state snapshot sequence
        """
        total_start_time = time.time()
        
        if self.verbose:
            print(f"🌍 Generating world state sequence mode (multi-threaded)")
            print(f"📋 Action sequence length: {len(action_sequence)}")
            print(f"🧠 Reasoning mode: {'Enabled' if enable_reasoning else 'Disabled'}")
            print(f"🔄 Maximum number of threads: {self.max_workers if self.max_workers else 'Unlimited'}")
        
        state_sequence = []
        
        # Add initial state (step 0), create safety check for the first action
        first_action_str = action_sequence[0] if action_sequence else None
        initial_snapshot = self._create_initial_snapshot(first_action_str, enable_reasoning)
        state_sequence.append(initial_snapshot)
        
        try:
            # Sequential action execution and parallel reasoning validation
            reasoning_futures = {}
            
            if self.verbose:
                print(f"\n🔄 [{time.strftime('%H:%M:%S')}] Sequential action execution and parallel reasoning validation")
                print(f"🧠 [{time.strftime('%H:%M:%S')}] Reasoning thread pool: {self.max_workers} working threads")
            
            # Create shared reasoning validation thread pool
            with ThreadPoolExecutor(max_workers=self.max_workers) as reasoning_executor:
                
                # Sequential execution of action sequence (sequential execution)
                for step_num, action_str in enumerate(action_sequence, 1):
                    step_start_time = time.time()  # Record step start time
                    
                    if self.verbose:
                        print(f"\n🎯 [{time.strftime('%H:%M:%S')}] === Start executing step {step_num} ===")
                        print(f"🎯 [{time.strftime('%H:%M:%S')}] Action: {action_str}")
                    
                    try:
                        # Get next action
                        next_action_str = None
                        if step_num < len(action_sequence):
                            next_action_str = action_sequence[step_num]
                        
                        # Sequential execution of action
                        action_success, action_errors = self._apply_action_to_world_copy(
                            self.world, action_str, step_num
                        )
                        
                        # Capture world snapshot after action execution
                        world_snapshot = None
                        if action_success:
                            world_snapshot = self._capture_world_snapshot(self.world)
                            if self.verbose:
                                print(f"📸 [{time.strftime('%H:%M:%S')}] Step {step_num} action execution successful, world snapshot captured")
                        else:
                            if self.verbose:
                                print(f"❌ [{time.strftime('%H:%M:%S')}] Step {step_num} action execution failed: {action_errors}")
                        
                        # Update context tracking
                        if action_success:
                            self._update_context_tracking(action_str)
                        
                        # Calculate step processing time (action execution time)
                        step_processing_time = time.time() - step_start_time
                        
                        # Submit parallel reasoning validation task (if enabled)
                        if enable_reasoning and world_snapshot:
                            if self.verbose:
                                print(f"🧠 [{time.strftime('%H:%M:%S')}] Submit step {step_num} to reasoning thread pool")
                            
                            # Record reasoning start time
                            reasoning_start_time = time.time()
                            future = reasoning_executor.submit(
                                self._validate_step_reasoning,
                                world_snapshot, step_num, action_str, next_action_str,
                                self.current_held_object, self.last_found_object
                            )
                            # 存储future和开始时间
                            reasoning_futures[step_num] = {
                                'future': future,
                                'start_time': reasoning_start_time
                            }
                        
                        # Create step snapshot (with correct processing time)
                        snapshot = WorldStateSnapshot(
                            step_number=step_num,
                            action_applied=action_str,
                            world_snapshot=world_snapshot if action_success else {},
                            reasoning_result=None,  # Reasoning result to be filled later
                            success=action_success,
                            errors=action_errors,
                            processing_time=step_processing_time,  # Actual step processing time
                            timestamp=time.strftime('%Y%m%d_%H%M%S')
                        )
                        
                        state_sequence.append(snapshot)
                        
                        if self.verbose:
                            status = "✅ Success" if action_success else "❌ Failure"
                            print(f"{status} [{time.strftime('%H:%M:%S')}] Step {step_num} completed (took {step_processing_time:.3f}s)")
                    
                    except Exception as e:
                        step_processing_time = time.time() - step_start_time
                        if self.verbose:
                            print(f"❌ Step {step_num} execution exception: {str(e)}")
                        
                        # Create failure snapshot
                        snapshot = WorldStateSnapshot(
                            step_number=step_num,
                            action_applied=action_str,
                            world_snapshot={},
                            reasoning_result=None,
                            success=False,
                            errors=[f"Action execution exception: {str(e)}"],
                            processing_time=step_processing_time,
                            timestamp=time.strftime('%Y%m%d_%H%M%S')
                        )
                        state_sequence.append(snapshot)
                
                # Collect parallel reasoning validation results
                if reasoning_futures:
                    if self.verbose:
                        print(f"\n🧠 [{time.strftime('%H:%M:%S')}] Waiting for {len(reasoning_futures)} reasoning validations to complete...")
                    
                    # Use as_completed to display real-time progress
                    completed_count = 0
                    future_items = [(step_num, info['future'], info['start_time']) for step_num, info in reasoning_futures.items()]
                    
                    for future in as_completed([item[1] for item in future_items]):
                        # Find the corresponding step number and start time
                        step_num = None
                        reasoning_start_time = None
                        for snum, fut, start_time in future_items:
                            if fut == future:
                                step_num = snum
                                reasoning_start_time = start_time
                                break
                        
                        completed_count += 1
                        reasoning_end_time = time.time()
                        reasoning_time = reasoning_end_time - reasoning_start_time if reasoning_start_time else 0
                        
                        try:
                            reasoning_result, has_interrupt = future.result()
                            
                            # Update corresponding step's reasoning result and total processing time
                            if step_num and step_num <= len(state_sequence):
                                state_sequence[step_num].reasoning_result = reasoning_result
                                # Update step total time: action execution time + reasoning validation time
                                state_sequence[step_num].processing_time += reasoning_time
                                
                            if self.verbose:
                                print(f"🧠 [{time.strftime('%H:%M:%S')}] Step {step_num} reasoning validation completed (reasoning time: {reasoning_time:.3f}s) ({completed_count}/{len(reasoning_futures)})")
                        
                        except Exception as e:
                            if self.verbose:
                                print(f"🧠 [{time.strftime('%H:%M:%S')}] Step {step_num} reasoning validation exception: {e}")
                            # Even if there is an exception, the reasoning time needs to be updated
                            if step_num and step_num <= len(state_sequence):
                                state_sequence[step_num].processing_time += reasoning_time
            
            # Calculate total time and print statistics
            total_end_time = time.time()
            total_processing_time = total_end_time - total_start_time
            
            successful_steps = sum(1 for s in state_sequence[1:] if s.success)
            if self.verbose:
                print(f"\n🎯 [{time.strftime('%H:%M:%S')}] Sequence generation completed: {successful_steps}/{len(action_sequence)} steps successful")
            
            # Time statistics always displayed,不受verbose控制
            self._print_timing_statistics(state_sequence, total_processing_time)
            
            return state_sequence
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Sequence generation exception: {e}")
            return state_sequence
    
    def _print_timing_statistics(self, state_sequence: List[WorldStateSnapshot], total_time: float):
        """Print time statistics"""
        print("\n" + "="*60)
        print("⏱️  Execution Time Statistics")
        print("="*60)
        
        # Total time statistics
        print(f"🕐 Total execution time: {total_time:.2f} seconds")
        
        # Step time statistics
        step_times = []
        successful_steps = 0
        
        for snapshot in state_sequence[1:]:  # Skip initial state
            if hasattr(snapshot, 'processing_time'):
                step_times.append(snapshot.processing_time)
                if snapshot.success:
                    successful_steps += 1
                
                status = "✅" if snapshot.success else "❌"
                print(f"{status} Step {snapshot.step_number}: {snapshot.processing_time:.2f}s - {snapshot.action_applied}")
        
        if step_times:
            print("-" * 60)
            print(f"📊 Step statistics:")
            print(f"   • Average step time: {sum(step_times)/len(step_times):.2f} seconds")
            print(f"   • Fastest step time: {min(step_times):.2f} seconds")
            print(f"   • Slowest step time: {max(step_times):.2f} seconds")
            print(f"   • Successful step count: {successful_steps}/{len(step_times)}")
            
            # Calculate parallel efficiency (if multi-threading)
            total_step_time = sum(step_times)
            if self.max_workers and self.max_workers > 1:
                theoretical_sequential_time = total_step_time
                parallel_efficiency = (theoretical_sequential_time / total_time) * 100
                print(f"   • Theoretical sequential time: {theoretical_sequential_time:.2f} seconds")
                print(f"   • Parallel acceleration ratio: {theoretical_sequential_time/total_time:.2f}x")
                print(f"   • Parallel efficiency: {parallel_efficiency:.1f}%")
        
        print("="*60)
    
    def _calculate_context_for_step(self, action_sequence: List[str], up_to_step: int) -> tuple[Optional[str], Optional[str]]:
        """
        Calculate the context state up to a specified step
        
        Args:
            action_sequence: Complete action sequence
            up_to_step: Calculate up to which step (not including)
            
        Returns:
            (current_held_object, last_found_object)
        """
        current_held = None
        last_found = None
        
        # Debugging step 5 context calculation
        is_debug_step = (up_to_step == 4)  # Step 5 needs to calculate the first 4 steps
        
        if self.verbose and is_debug_step:
            print(f"🔍 Context calculation started: Analyzing the first {up_to_step} steps")
        
        # Simulate executing previous actions to calculate context
        for i in range(min(up_to_step, len(action_sequence))):
            action_str = action_sequence[i]
            parsed_actions = parse_action_sequence([action_str])
            if parsed_actions:
                action_name, parameters = parsed_actions[0]
                
                if self.verbose and is_debug_step:
                    print(f"🔍 Step {i+1}: {action_str} -> {action_name}, {parameters}")
                
                if action_name == 'find':
                    last_found = parameters.get('object')
                    if self.verbose and is_debug_step:
                        print(f"🔍   Update last_found: {last_found}")
                elif action_name == 'pick':
                    current_held = parameters.get('object')
                    if self.verbose and is_debug_step:
                        print(f"🔍   Update current_held: {current_held}")
                elif action_name in ['put', 'drop', 'throw']:
                    current_held = None
                    if self.verbose and is_debug_step:
                        print(f"🔍   Clear current_held")
        
        if self.verbose and is_debug_step:
            print(f"🔍 Context calculation completed: Holding={current_held}, Found={last_found}")
        
        return current_held, last_found
    
    def _sync_world_with_context(self, step_world, current_held_object: str, last_found_object: str, step_num: int):
        """
        Sync the world copy based on the context state, making the copy contain the effects of previous steps
        
        Args:
            step_world: Step world copy
            current_held_object: Object that should be held currently
            last_found_object: Object found recently
            step_num: Current step number
        """
        if self.verbose:
            print(f"🧵 [{time.strftime('%H:%M:%S')}|T{threading.get_ident()%10000:04d}] 🔄 Syncing world copy state")
        
        try:
            # If the context indicates that the robot should hold an object, but the robot's hand is empty in the world
            if current_held_object:
                # Check the robot's current state
                robot_instance = None
                for individual in step_world.individuals():
                    if hasattr(individual, 'name') and 'my_robot' in str(individual.name):
                        robot_instance = individual
                        break
                
                if robot_instance:
                    # Check if the robot already holds the target object
                    is_holding_target = False
                    for prop in robot_instance.get_properties():
                        if 'isHolding' in str(prop):
                            for value in prop[robot_instance]:
                                if str(value) == current_held_object:
                                    is_holding_target = True
                                    break
                    
                    if not is_holding_target:
                        # Need to simulate pick action effects
                        if self.verbose:
                            print(f"🧵 [{time.strftime('%H:%M:%S')}|T{threading.get_ident()%10000:04d}] 🔄 Simulate pick effect: {current_held_object}")
                        
                        # Use ActionExecutor to simulate pick action
                        temp_executor = ActionExecutor(step_world, verbose=False)
                        pick_success, _ = temp_executor.execute_action('pick', {
                            'agent': 'my_robot',
                            'object': current_held_object
                        })
                        
                        if self.verbose:
                            if pick_success:
                                print(f"🧵 [{time.strftime('%H:%M:%S')}|T{threading.get_ident()%10000:04d}] ✅ Sync completed: Robot now holds {current_held_object}")
                            else:
                                print(f"🧵 [{time.strftime('%H:%M:%S')}|T{threading.get_ident()%10000:04d}] ⚠️ Sync failed: Unable to let robot hold {current_held_object}")
                
        except Exception as e:
            if self.verbose:
                print(f"🧵 [{time.strftime('%H:%M:%S')}|T{threading.get_ident()%10000:04d}] ❌ World copy sync exception: {e}")
    
    def _validate_step_reasoning(self, world_snapshot: Dict[str, Any], step_num: int, 
                               action_str: str, next_action_str: str = None,
                               current_held_object: str = None, last_found_object: str = None):
        """
        Parallel reasoning validation method
        
        Args:
            world_snapshot: World snapshot after action execution
            step_num: Step number
            action_str: Action string
            next_action_str: Next action
            current_held_object: Current held object
            last_found_object: Recently found object
            
        Returns:
            (reasoning_result, has_interrupt_danger)
        """
        thread_id = threading.get_ident() % 10000
        if self.verbose:
            print(f"🧠 [{time.strftime('%H:%M:%S')}|T{thread_id:04d}] Start reasoning validation step {step_num}")
        
        try:
            reasoning_result, has_interrupt = self.reasoning_validator.validate_step_safety(
                world_snapshot=world_snapshot,
                step_num=step_num,
                action_str=action_str,
                next_action_str=next_action_str,
                current_held_object=current_held_object,
                last_found_object=last_found_object
            )
            
            if self.verbose:
                if has_interrupt:
                    print(f"🧠 [{time.strftime('%H:%M:%S')}|T{thread_id:04d}] ⚠️ Step {step_num} detected danger")
                else:
                    print(f"🧠 [{time.strftime('%H:%M:%S')}|T{thread_id:04d}] ✅ Step {step_num} reasoning validation safe")
            
            return reasoning_result, has_interrupt
            
        except Exception as e:
            if self.verbose:
                print(f"🧠 [{time.strftime('%H:%M:%S')}|T{thread_id:04d}] ❌ Step {step_num} reasoning validation exception: {e}")
            return None, False
    
    def _update_context_tracking(self, action_str: str):
        """
        Update context tracking based on action string
        
        Args:
            action_str: Action string
        """
        with self._lock:  # Thread safety
            parsed_actions = parse_action_sequence([action_str])
            if parsed_actions:
                action_name, parameters = parsed_actions[0]
                if action_name == 'find':
                    self.last_found_object = parameters.get('object')
                    if self.verbose:
                        print(f"   📝 Update last_found_object: {self.last_found_object}")
                elif action_name == 'pick':
                    self.current_held_object = parameters.get('object')
                    if self.verbose:
                        print(f"   📝 Update current_held_object: {self.current_held_object}")
                elif action_name in ['put', 'drop', 'throw']:
                    self.current_held_object = None
                    if self.verbose:
                        print(f"   📝 Clear current_held_object")
    
    def _create_initial_snapshot(self, first_action_str: str = None, enable_reasoning: bool = True) -> WorldStateSnapshot:
        """Create initial state snapshot"""
        world_snapshot = self.world_state_manager.capture_world_state()
        reasoning_result = None
        
        # If reasoning is enabled and there is a first action, create an action instance for safety detection
        if enable_reasoning and first_action_str:
            if self.verbose:
                print(f"   🧠 [Initial state] Create safety detection for first action: {first_action_str}")
            
            reasoning_result, has_interrupt_danger = self.reasoning_validator.validate_step_safety(
                world_snapshot=world_snapshot,
                step_num=0,
                action_str='INITIAL_STATE',
                next_action_str=first_action_str,
                current_held_object=self.current_held_object,
                last_found_object=self.last_found_object
            )
            
            if has_interrupt_danger:
                if self.verbose:
                    print(f"   🚨 [Initial state] Detected danger in the first action")
        
        return WorldStateSnapshot(
            step_number=0,
            action_applied='INITIAL_STATE',
            world_snapshot=world_snapshot,
            reasoning_result=reasoning_result,
            success=True,
            errors=[],
            timestamp=time.strftime('%Y%m%d_%H%M%S')
        )
    
    def _clone_world_for_step(self, step_num: int):
        """Create world copy for step"""
        try:
            if self.verbose:
                print(f"   🔄 Create world copy for step {step_num}...")
            
            # Capture current world state
            current_world_snapshot = self.world_state_manager.capture_world_state()
            if self.verbose:
                print(f"   🔍 Step {step_num} copy creation - Captured instance count: {len(current_world_snapshot.get('individuals', {}))}")
            
            # Use WorldStateManager's method to rebuild the world
            reconstructed_data = self.world_state_manager.reconstruct_world_from_snapshot(current_world_snapshot)
            
            if reconstructed_data:
                step_world, _ = reconstructed_data # We only need the world instance here
                if self.verbose:
                    print(f"   ✅ Step {step_num} world copy created successfully")
                return step_world
            else:
                if self.verbose:
                    print(f"   ⚠️ World copy creation failed: Unable to rebuild world state")
                return None
            
        except Exception as e:
            print(f"   ⚠️ World copy creation failed: {e}")
            return None
    
    def _create_reasoning_copy_from_snapshot(self, world_snapshot):
        """
        Create reasoning copy based on world snapshot
        
        Args:
            world_snapshot: World snapshot
            
        Returns:
            Reasoning world copy
        """
        try:
            if not world_snapshot:
                if self.verbose:
                    print(f"   ⚠️ Reasoning copy creation failed: Snapshot is empty")
                return None
            
            # 基于快照重建推理副本
            reconstructed_data = self.world_state_manager.reconstruct_world_from_snapshot(world_snapshot)
            
            if reconstructed_data:
                reasoning_world, _ = reconstructed_data
                if self.verbose:
                    print(f"   🧠 Based on snapshot, reasoning copy created successfully")
                return reasoning_world
            else:
                if self.verbose:
                    print(f"   ⚠️ Based on snapshot, reasoning copy creation failed")
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Based on snapshot, reasoning copy creation failed: {e}")
            return None
    
    def _apply_action_to_world_copy(self, world_copy, action_str: str, step_num: int) -> tuple:
        """Apply action to world copy"""
        try:
            # Parse action
            parsed_actions = parse_action_sequence([action_str])
            if not parsed_actions:
                return False, [f"Unable to parse action: {action_str}"]
            
            action_name, parameters = parsed_actions[0]
            
            # Create independent ActionExecutor for the copy, passing current state
            step_action_executor = ActionExecutor(world_copy, verbose=self.verbose)
            step_action_executor.currently_holding = self.current_held_object
            step_action_executor.last_found_object = self.last_found_object
            
            # 🔑 Key fix: Perform action on the copy, not the main world
            action_success = step_action_executor.apply_action_effects(action_name, parameters)
            
            # Update context tracking
            if action_success:
                if action_name == 'find':
                    self.last_found_object = parameters.get('object')
                    if self.verbose:
                        print(f"   📝 Update last_found_object: {self.last_found_object}")
                elif action_name == 'pick':
                    self.current_held_object = parameters.get('object')
                    if self.verbose:
                        print(f"   📝 Update current_held_object: {self.current_held_object}")
                elif action_name == 'put':
                    self.current_held_object = None
                    if self.verbose:
                        print(f"   📝 Clear current_held_object")
            
            errors = [] if action_success else [f"Action execution failed: {action_str}"]
            return action_success, errors
            
        except Exception as e:
            error_msg = f"Action application failed: {e}"
            if self.verbose:
                print(f"   ❌ {error_msg}")
                import traceback
                traceback.print_exc()
            return False, [error_msg]
    
    def _is_valid_object_name(self, obj):
        """Validate if the object is a valid instance name"""
        if not obj or not isinstance(obj, str):
            return False
        
        # Check for invalid patterns
        invalid_patterns = [
            'terms.description',
            'AnnotationPropertyClass',
            'owl.Thing',
            'owl.'
        ]
        
        for pattern in invalid_patterns:
            if pattern in str(obj):
                return False
        
        return True
    
    
    
    def _capture_world_snapshot(self, world) -> Dict[str, Any]:
        """Capture world state snapshot"""
        temp_manager = WorldStateManager(world)
        return temp_manager.capture_world_state()
    
    
    def _update_main_world_from_copy(self, world_copy):
        """Update main world state from copy"""
        try:
            if self.verbose:
                print("   🔄 Main world state updating...")
            
            # Replace main world with the copy
            self.world = world_copy
            
            # Update components that depend on world state
            self.action_executor = ActionExecutor(self.world, verbose=self.verbose)
            self.world_state_manager = WorldStateManager(self.world, verbose=self.verbose)
            
            if self.verbose:
                print("   ✅ Main world state updated successfully")
            
        except Exception as e:
            print(f"   ❌ Main world state update failed: {e}")
    
    def _update_main_world_from_snapshot(self, clean_snapshot: Dict[str, Any]):
        """
        Update main world state from clean snapshot, avoiding FusionClass pollution
        
        Args:
            clean_snapshot: Clean snapshot captured before reasoning
        """
        try:
            if self.verbose:
                print("   📦 Reconstructing main world state from clean snapshot...")
            
            # 使用WorldStateManager从快照重建世界
            reconstructed_data = self.world_state_manager.reconstruct_world_from_snapshot(clean_snapshot)
            
            if reconstructed_data:
                new_world, _ = reconstructed_data
                
                # Update main world
                self.world = new_world
                
                # Update components that depend on world state
                self.action_executor = ActionExecutor(self.world, verbose=self.verbose)
                self.world_state_manager = WorldStateManager(self.world, verbose=self.verbose)
                
                if self.verbose:
                    print("   ✅ Main world updated successfully from clean snapshot (original class names)")
            else:
                if self.verbose:
                    print("   ⚠️ Failed to reconstruct world from snapshot")
        
        except Exception as e:
            print(f"   ❌ Failed to update main world from snapshot: {e}")
            import traceback
            traceback.print_exc()
    
    def _print_sequence_statistics(self, state_sequence: List[WorldStateSnapshot]):
        """Print sequence statistics"""
        successful_steps = sum(1 for state in state_sequence[1:] if state.success)
        failed_steps = sum(1 for state in state_sequence[1:] if not state.success)
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
        
        print(f"\n🌍 World state sequence generation completed:")
        print(f"   Total states: {len(state_sequence)} (including initial state)")
        print(f"   Successful steps: {successful_steps}")
        print(f"   Failed steps: {failed_steps}")
        print(f"   Total reasoning time: {total_reasoning_time:.3f}s")
        print(f"   New inferences: {total_new_inferences}")
    
    def export_sequence_to_json(self, state_sequence: List[WorldStateSnapshot], output_file: str):
        """Export state sequence to JSON file"""
        import json
        
        try:
            # Convert to serializable format
            serializable_sequence = []
            for snapshot in state_sequence:
                serializable_snapshot = {
                    'step_number': snapshot.step_number,
                    'action_applied': snapshot.action_applied,
                    'world_snapshot': snapshot.world_snapshot,
                    'reasoning_result': snapshot.reasoning_result,
                    'success': snapshot.success,
                    'errors': snapshot.errors,
                    'timestamp': snapshot.timestamp
                }
                serializable_sequence.append(serializable_snapshot)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_sequence, f, indent=2, ensure_ascii=False)
            
            if self.verbose:
                print(f"📄 State sequence exported to: {output_file}")
            
        except Exception as e:
            print(f"❌ Failed to export state sequence: {e}")
            raise