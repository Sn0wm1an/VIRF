import subprocess
import time
import os
import concurrent.futures
from pathlib import Path

# Total number of scenes to process
TOTAL_SCENES = 30
# Maximum number of concurrent threads (adjust based on your CPU cores)
MAX_WORKERS = 8
# Project main directory
project_root = Path(__file__).parent
# Parent directory containing all scene images
VISUAL_DATAS_DIR = project_root / "visual_datas"
# Directory for final output files
OUTPUT_DIR = project_root / "output_1"
# Log file for recording execution times
TIME_LOG_FILE = "execution_times.log"


def run_scene_processing(scene_number):
    """
    Run main.py script for a single scene and return execution time.

    Args:
        scene_number (int): The scene number.

    Returns:
        tuple: (scene_number, execution_time) or (scene_number, error_message).
    """
    scene_dir_name = f"visual_data{scene_number}"
    image_dir = f"{VISUAL_DATAS_DIR}/{scene_dir_name}"
    output_file = f"{OUTPUT_DIR}/environment{scene_number}.json"

    # Check if input directory exists
    if not os.path.isdir(image_dir):
        error_message = f"Error: Input directory does not exist - {image_dir}"
        print(error_message)
        return scene_number, error_message

    # Build command line instruction
    command = [
        "python3",
        "main.py",
        "--image_dir", image_dir,
        "--output_file", output_file
    ]

    print(f"Starting to process scene {scene_number}...")
    start_time = time.time()

    try:
        # Set environment variables and execute subprocess
        env = os.environ.copy()
        env["LOG_LEVEL"] = "DEBUG"
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'  # Ensure correct encoding
        )
        # Print subprocess output for debugging
        # print(f"--- Output (Scene {scene_number}) ---\n{result.stdout}\n--------------------")

    except subprocess.CalledProcessError as e:
        # Capture error if script returns non-zero exit code
        error_message = f"Scene {scene_number} processing failed. Return code: {e.returncode}"
        print(error_message)
        print(f"--- Error Output (Scene {scene_number}) ---\n{e.stderr}\n--------------------")
        return scene_number, f"Processing failed: {e.stderr[:200]}..."  # Return partial error info
    except Exception as e:
        error_message = f"Unknown error occurred while running scene {scene_number}: {e}"
        print(error_message)
        return scene_number, error_message

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Scene {scene_number} processing completed, elapsed time: {elapsed_time:.2f} seconds.")
    return scene_number, elapsed_time


def main():
    """
    Main function that uses multi-threading to run all scene processing in parallel.
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get list of scenes to process
    scenes_to_process = range(1, TOTAL_SCENES + 1)

    execution_results = {}
    total_start_time = time.time()

    print(f"Starting parallel processing of {TOTAL_SCENES} scenes, max concurrency: {MAX_WORKERS}...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_scene = {executor.submit(run_scene_processing, i): i for i in scenes_to_process}

        # Wait for tasks to complete and collect results
        for future in concurrent.futures.as_completed(future_to_scene):
            scene_num = future_to_scene[future]
            try:
                scene_number, result = future.result()
                execution_results[scene_number] = result
            except Exception as exc:
                print(f"Scene {scene_num} generated an exception during execution: {exc}")
                execution_results[scene_num] = f"Execution exception: {exc}"

    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time
    print(f"\nAll scene processing completed. Total elapsed time: {total_elapsed_time:.2f} seconds.")

    # --- Record execution times to file ---
    print(f"Recording execution times to {TIME_LOG_FILE}...")
    with open(TIME_LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"Total runtime for all scenes: {total_elapsed_time:.2f} seconds\n")
        f.write("-" * 30 + "\n")
        # Write sorted by scene number
        for scene_number in sorted(execution_results.keys()):
            result = execution_results[scene_number]
            if isinstance(result, float):
                f.write(f"Scene {scene_number}: {result:.2f} seconds\n")
            else:
                f.write(f"Scene {scene_number}: {result}\n")  # Record error information

    print("✅ All tasks completed!")


if __name__ == "__main__":
    main()