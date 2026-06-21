"""
Phi-2 Model Loading Debugger

This script systematically tests the model loading process
to identify the exact failure point.
"""

import os
import sys
import logging
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

def check_file_integrity():
    """Check if GGUF file exists and has correct properties."""
    print("\n" + "="*60)
    print("STEP 1: FILE INTEGRITY CHECK")
    print("="*60)
    
    model_path = os.path.expanduser(
        "~/rag_elderly_care_robot_simulation/llm_models/phi-2-q4.gguf"
    )
    
    print(f"Model path: {model_path}")
    
    # Check existence
    if not os.path.exists(model_path):
        print("❌ Model file NOT FOUND")
        return False
    
    print("✅ Model file exists")
    
    # Check size
    size_bytes = os.path.getsize(model_path)
    size_gb = size_bytes / (1024**3)
    size_mb = size_bytes / (1024**2)
    
    print(f"✅ File size: {size_gb:.2f} GB ({size_mb:.0f} MB)")
    
    # Check if file is readable
    if not os.access(model_path, os.R_OK):
        print("❌ File is NOT readable")
        return False
    
    print("✅ File is readable")
    
    # Check file magic bytes (GGUF files start with "GGUF")
    try:
        with open(model_path, 'rb') as f:
            magic = f.read(4)
            if magic == b'GGUF':
                print("✅ Valid GGUF magic bytes detected")
                return True
            else:
                print(f"❌ Invalid magic bytes: {magic}")
                print("   Expected: b'GGUF'")
                return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def check_llama_cpp_installation():
    """Check if llama-cpp-python is installed correctly."""
    print("\n" + "="*60)
    print("STEP 2: LLAMA-CPP-PYTHON INSTALLATION")
    print("="*60)
    
    try:
        import llama_cpp
        print(f"✅ llama_cpp module imported")
        print(f"   Location: {llama_cpp.__file__}")
        
        from llama_cpp import Llama
        print(f"✅ Llama class imported successfully")
        
        # Check version
        if hasattr(llama_cpp, '__version__'):
            print(f"   Version: {llama_cpp.__version__}")
        
        return True
    
    except ImportError as e:
        print(f"❌ Failed to import llama_cpp: {e}")
        print("\nInstall with: pip install llama-cpp-python")
        return False


def test_model_loading_verbose():
    """Test model loading with maximum verbosity."""
    print("\n" + "="*60)
    print("STEP 3: MODEL LOADING TEST (VERBOSE)")
    print("="*60)
    
    try:
        from llama_cpp import Llama
        
        model_path = os.path.expanduser(
            "~/rag_elderly_care_robot_simulation/llm_models/phi-2-q4.gguf"
        )
        
        print(f"\nAttempting to load model from:")
        print(f"  {model_path}")
        print(f"\nParameters:")
        print(f"  - n_ctx: 2048")
        print(f"  - n_threads: 4")
        print(f"  - n_gpu_layers: 0 (CPU only)")
        print(f"  - verbose: True")
        
        print(f"\nLoading... (this may take 30-60 seconds)")
        
        # Try with verbose=True to get more info
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0,
            verbose=True  # Enable verbose output
        )
        
        print("\n✅ MODEL LOADED SUCCESSFULLY!")
        print(f"   Model type: {type(model)}")
        print(f"   Context size: {model.n_ctx}")
        
        return True, model
    
    except Exception as e:
        print(f"\n❌ MODEL LOADING FAILED")
        print(f"   Error: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        
        import traceback
        print(f"\nFull traceback:")
        traceback.print_exc()
        
        return False, None


def test_model_inference(model):
    """Test if model can generate text."""
    print("\n" + "="*60)
    print("STEP 4: MODEL INFERENCE TEST")
    print("="*60)
    
    if model is None:
        print("❌ Model not loaded, skipping inference test")
        return False
    
    try:
        print("\nTesting inference with simple prompt...")
        prompt = "What is hypertension?"
        
        print(f"Prompt: {prompt}")
        print(f"Max tokens: 50")
        print(f"\nGenerating... (this may take 10-30 seconds)")
        
        response = model(
            prompt=prompt,
            max_tokens=50,
            temperature=0.7,
            top_p=0.95
        )
        
        generated_text = response['choices'][0]['text']
        
        print(f"\n✅ INFERENCE SUCCESSFUL!")
        print(f"Generated text: {generated_text}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ INFERENCE FAILED")
        print(f"   Error: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        
        import traceback
        traceback.print_exc()
        
        return False


def main():
    """Run all debugging steps."""
    print("\n" + "="*60)
    print("PHI-2 MODEL LOADING DEBUGGER")
    print("="*60)
    
    # Step 1: File integrity
    if not check_file_integrity():
        print("\n❌ File integrity check FAILED")
        print("   Recommendation: Re-download the model")
        return
    
    # Step 2: Installation check
    if not check_llama_cpp_installation():
        print("\n❌ llama-cpp-python installation FAILED")
        print("   Recommendation: Reinstall with: pip install llama-cpp-python")
        return
    
    # Step 3: Loading test
    success, model = test_model_loading_verbose()
    
    if not success:
        print("\n❌ Model loading FAILED")
        print("\nRECOMMENDATIONS:")
        print("1. Check GGUF file compatibility")
        print("2. Try alternative quantization (Q5_K_M instead of Q4_K_M)")
        print("3. Update llama-cpp-python: pip install --upgrade llama-cpp-python")
        print("4. Try different GGUF model")
        return
    
    # Step 4: Inference test (if loading succeeded)
    if success:
        test_model_inference(model)
    
    print("\n" + "="*60)
    print("DEBUGGING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
