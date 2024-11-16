import os
import sys

# Add the src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
sys.path.insert(0, project_root)

# Now import and run the api_model
from benchmarks.mmlu_pro import main

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
    
# python src/run_mmlu_pro.py -o 4o-mini--flash-1-5 -m1 openai/gpt-4o-mini -m2 google/gemini-flash-1.5-exp -a business -s 1