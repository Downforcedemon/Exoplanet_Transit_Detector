import os
import json
import matplotlib.pyplot as plt
import logging
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging for this module
LOG_FILE = "visualize_transits_module/logs/visualize_transits.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def generate_visualization(results_path):
    """Generate a plot based on the results JSON file."""
    try:
        # Load the JSON results
        with open(results_path, 'r') as f:
            results = json.load(f)

        # Extract relevant metrics
        period = results.get("period", 0)
        duration = results.get("duration", 0)
        depth = results.get("depth", 0)
        power = results.get("power", 0)

        logging.debug(f"Loaded results from {results_path}: Period={period}, Duration={duration}, Depth={depth}, Power={power}")

        # Generate a simple bar plot for demonstration
        metrics = ["Period", "Duration", "Depth", "Power"]
        values = [period, duration, depth, power]

        plt.bar(metrics, values, color="skyblue")
        plt.xlabel("Transit Metrics")
        plt.ylabel("Values")
        plt.title("Transit Detection Metrics")

        # Save the plot in the visualize module's data folder
        output_path = os.path.join("visualize_transits_module", "data", 
                                   os.path.basename(results_path).replace("_results.json", "_metrics.png"))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path)
        logging.debug(f"Visualization saved to {output_path}")

    except Exception as e:
        logging.error(f"Error generating visualization: {e}")
        raise

def trigger_db_writer(tic_id):
    try:
        logging.info(f"Triggering db_writer for TIC ID: {tic_id}")
        subprocess.run(
            ["python",
            "visualize_transits_module/scripts/db_writer.py",
            tic_id], 
            check=True)
        logging.info(f"Successfully triggered db_writer for TIC ID: {tic_id}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error triggering db_writer: {e}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        logging.error("Usage: python generate_plot.py <results_path>")
        exit(1)
    results_path = sys.argv[1]
    if not os.path.exists(results_path):
        logging.error(f"Results file not found: {results_path}")
        exit(1)

    # Call the visualization function
    try:
        visualization_path = generate_visualization(results_path)
        logging.info("Visualization generated successfully.")

        # Extract TIC ID from the filename
        filename = os.path.basename(results_path)
        if filename.startswith("TIC") and "_processed_results.json" in filename:
            tic_id = filename.split("_processed_results.json")[0]
            logging
        else:
            raise ValueError(f"Invalid filename format: {filename}")

        # Trigger db_writer
        trigger_db_writer(tic_id)
        logging.info("db_writer triggered successfully.")

    except Exception as e:
        logging.error(f"Error generating visualization: {e}")
        exit(1)

    exit(0)
    
    