#!/usr/bin/env python3
"""Run evaluation script for Geotech Q&A Service."""

import subprocess
import sys
import os
from pathlib import Path


def run_evaluation():
    """Run the evaluation script."""
    print("🔬 Running Geotech Q&A Service Evaluation")
    print("=" * 60)
    
    # Check if evaluation script exists
    eval_script = Path("app/eval/evaluation_script.py")
    if not eval_script.exists():
        print("❌ Evaluation script not found: app/eval/evaluation_script.py")
        return 1
    
    # Check if test dataset exists
    test_dataset = Path("app/eval/test_qa.json")
    if not test_dataset.exists():
        print("❌ Test dataset not found: app/eval/test_qa.json")
        return 1
    
    # Run evaluation
    try:
        print("🚀 Starting evaluation...")
        result = subprocess.run([
            sys.executable, str(eval_script)
        ], check=True, capture_output=False)
        
        print("✅ Evaluation completed successfully!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Evaluation failed with exit code: {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")
        return 1

def main():
    """Main function."""
    return run_evaluation()


if __name__ == "__main__":
    sys.exit(main())
