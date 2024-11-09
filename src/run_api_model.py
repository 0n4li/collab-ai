import os
import sys

# Add the src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
sys.path.insert(0, project_root)

# Now import and run the api_model
from api.collab_api_model import main

if __name__ == "__main__":
    main()
