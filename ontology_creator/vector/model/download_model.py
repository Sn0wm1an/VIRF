#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model download script
Directly download the all-MiniLM-L6-v2 model to the .cache directory
Adapted for the Chinese mainland network environment
"""

import os
import shutil
from huggingface_hub import snapshot_download

def download_model():
    """Download model to .cache directory"""
    
    # Set cache directory
    cache_dir = os.path.join(os.getcwd(), '.cache')
    model_dir = os.path.join(cache_dir, 'sentence-transformers_all-MiniLM-L6-v2')
    os.makedirs(cache_dir, exist_ok=True)
    
    print("🔽 Start downloading model all-MiniLM-L6-v2...")
    print(f"📁 Cache directory: {cache_dir}")
    print(f"📁 Model directory: {model_dir}")
    
    # Check if model already exists
    if os.path.exists(model_dir) and os.listdir(model_dir):
        print("✅ Model already exists, skipping download")
        return test_model(model_dir)
    
    # Try multiple mirror sources
    mirrors = [
        "https://hf-mirror.com",
    ]
    
    for mirror in mirrors:
        try:
            print(f"🌐 Try downloading from {mirror}...")
            
            # Directly download model files
            snapshot_download(
                repo_id="sentence-transformers/all-MiniLM-L6-v2",
                cache_dir=cache_dir,
                local_dir=model_dir,
                endpoint=mirror,
            )
            
            print("✅ Model downloaded successfully")
            return test_model(model_dir)
            
        except Exception as e:
            print(f"❌ Download failed from {mirror}: {e}")
            if os.path.exists(model_dir):
                shutil.rmtree(model_dir)
            continue
    
    print("❌ All download sources failed")
    print("💡 Suggestions:")
    print("   1. Check network connection")
    print("   2. Try using VPN")
    print("   3. Manually download model files")

def test_model(model_dir):
    """Test if the model works normally"""
    try:
        from sentence_transformers import SentenceTransformer
        
        print("🧪 Testing model...")
        model = SentenceTransformer(model_dir, device='cpu')
        
        test_text = "test text"
        vector = model.encode(test_text)
        print(f"✅ Model test passed, vector dimension: {len(vector)}")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

if __name__ == "__main__":
    download_model()
