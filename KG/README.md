# Scene Knowledge Graph Generator

A scene knowledge graph generator that creates ontology-compatible knowledge graphs from scene images for ontological reasoning.

## Installation

```bash
pip install -r requirements.txt
```

## Environment Configuration

Copy the `env_example` file to `.env` and configure API keys:

```bash
API_KEY="your-api-key"
BASE_URL="your-api-base-url"
MODEL="your-model-name"
DDS_TOKEN="your-dds-token"  # Only required when using DINOX method
```

## Usage

### Basic Usage

```bash
python main.py --image_dir "visual_data_test"
```

### Specify Detection Method

Using DINOX method (default):

```bash
python main.py --image_dir "visual_data_test" --detection_method DINOX
```

Using VLM method:

```bash
python main.py --image_dir "visual_data_test" --detection_method VLM
```

## Parameters

- `--image_dir`: Directory containing scene images, default is "visual_data"
- `--detection_method`: Object detection method, options are DINOX or VLM, default is DINOX
- `--output_file`: Output file path, default is "output/environment.json"

## Output

The program analyzes scene images, detects objects, and generates a knowledge graph containing the following information:

- Object instances and categories
- Object material properties
- Object state information
- Spatial relationships between objects

Results are saved in the `output/environment.json` file in ontology-compatible instance and assertion structure format.

## Batch Processing

### Parallel Batch Processing of Multiple Scenes

Use the `evaluate/run_parallel.py` script to process multiple scenes in parallel:

```bash
cd evaluate
python run_parallel.py
```

Script features:

- Automatically processes 1-30 scenes
- Supports multi-threaded parallel processing
- Input directory: `visual_datas/visual_data{N}`
- Output files: `output_1/environment{N}.json`
- Generates execution time logs

### Accuracy Calculation

Use `evaluate/accuracy_calculator.py` to calculate accuracy between generated results and AI2THOR standard scenes:

```bash
cd evaluate
python accuracy_calculator.py
```

Script features:

- Compares generated object categories with AI2THOR official scenes
- Calculates detection accuracy
- Processes evaluation results for 1-30 scenes