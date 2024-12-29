from astroquery.mast import Catalogs
import os
import time
import logging
import json
import subprocess
import warnings
from datetime import datetime

def get_project_root():
    """Get the absolute path to the project's root directory."""
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
    return project_root

def load_config():
    """Load the configuration file and adjust relative paths."""
    try:
        project_root = get_project_root()
        config_path = os.path.join(project_root, "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)

        # Adjust paths to absolute paths
        for key in ["output_path", "fetch_star_ids_log", "raw_data_dir", "star_ids_file", "fetch_star_data_log"]:
            if key in config:
                config[key] = os.path.join(project_root, config[key])
        return config
    except FileNotFoundError:
        print("Configuration file not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {e}")
        return None

def setup_logging(config, log_key):
    """Set up logging configuration for consistent logging in terminal and log files."""
    try:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(config[log_key]), exist_ok=True)

        # Create handlers
        file_handler = logging.FileHandler(config[log_key])
        console_handler = logging.StreamHandler()

        # Set log levels
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)

        # Define formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Get the root logger and configure it
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Capture warnings
        logging.captureWarnings(True)
        warnings.simplefilter("always")

        logging.debug("Logging setup complete.")
        return True
    except Exception as e:
        print(f"Error setting up logging: {e}")
        return False

def query_star_catalog(config):
    """Query the MAST star catalog with parameters from config."""
    try:
        logging.debug("Starting query...")
        start_time = time.time()

        query_results = Catalogs.query_criteria(
            catalog=config["catalog"],
            Tmag=(
                config["query_parameters"]["brightness_range"][0],
                config["query_parameters"]["brightness_range"][1]
            )
        )

        query_duration = time.time() - start_time
        logging.debug(f"Query completed in {query_duration:.2f} seconds.")

        if len(query_results) > 0:
            logging.debug(f"Sample of fetched star IDs: {query_results[:5]['ID']}")

        if len(query_results) < config["num_star_ids"]:
            logging.warning(f"Only {len(query_results)} stars fetched (fewer than {config['num_star_ids']}).")
        else:
            logging.debug(f"Successfully fetched {len(query_results)} stars from {config['catalog']}.")
        return query_results

    except Exception as e:
        logging.error(f"Error querying the star catalog: {e}")
        return None

def save_star_ids(query_results, config):
    """Save star IDs to output file."""
    try:
        logging.debug("Saving star IDs to file...")
        os.makedirs(os.path.dirname(config["output_path"]), exist_ok=True)
        
        with open(config["output_path"], "w") as file:
            for i, row in enumerate(query_results[:config["num_star_ids"]]):
                file.write(f"TIC {row['ID']}\n")
                logging.debug(f"Saving star ID: TIC {row['ID']}")
        return True
    except Exception as e:
        logging.error(f"Error saving star IDs: {e}")
        return False

def trigger_fetch_star_data():
    """Trigger the fetch_star_data.py script after saving TIC IDs."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fetch_star_data_script = os.path.join(script_dir, "fetch_star_data.py")
        if os.path.exists(fetch_star_data_script):
            logging.debug("Triggering fetch_star_data.py...")
            subprocess.run(["python", fetch_star_data_script], check=True)
            logging.debug("Successfully triggered fetch_star_data.py")
        else:
            logging.error(f"fetch_star_data.py not found at {fetch_star_data_script}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error triggering fetch_star_data.py: {e}")

def main():
    try:
        config = load_config()
        if not config:
            return False

        if not setup_logging(config, "fetch_star_ids_log"):
            return False

        logging.debug("Fetching star IDs from MAST catalog...")
        results = query_star_catalog(config)

        if results and save_star_ids(results, config):
            logging.debug("Star IDs saved successfully.")
            trigger_fetch_star_data()
            return True
    except Exception as e:
        logging.error(f"Unexpected error in main: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        logging.error("Pipeline execution failed")
        exit(1)
