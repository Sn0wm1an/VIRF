# Ontology Generator

A comprehensive **ontology generation and management system** that leverages **Large Language Models (LLMs)** to automatically generate, validate, and manage OWL ontologies with advanced Manchester Syntax support and vector processing capabilities.

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_model
```

### Vector Model Setup (Optional)
Used for ontology vectorization and semantic matching, recommended to improve rule generation quality.

**Download vector model:**
```bash
python vector/model/download_model.py
```

**Run incremental vectorization process:**
```bash
python vector/run_incremental_vectorization.py
```

## Quick Start

### **Ontology Generation**
```bash
# Run the complete pipeline
python test.py --step all --input "Sharp knife near hot stove poses danger" --debug

# Step-by-step processing
python test.py --step 1  --debug # LLM generating Manchester JSON
python test.py --step 2  --debug # Vector validation  
python test.py --step 3  --debug # Hierarchy structure analysis
python test.py --step 4  --debug # Ontology writing
```