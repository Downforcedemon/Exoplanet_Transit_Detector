import sys
import os
import json

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the necessary functions
from Data_Download_Module.scripts.fetch_star_data import fetch_star_data, load_config

# Load configuration
config = load_config()

# Test fetch star data function
star_id = "TIC_338995234"
result = fetch_star_data(star_id, config)

if result is not None:
    print(f"Successfully processed {star_id}")
else:
    print(f"Failed to process {star_id}")
