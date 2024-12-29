import time
import os
import lightkurve as lk
import logging
import subprocess
import json
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
        # Adjust relative paths to absolute paths
        for key in ["output_path", "fetch_star_ids_log", "raw_data_dir", "star_ids_file", "fetch_star_data_log"]:
            if key in config:
                config[key] = os.path.join(project_root, config[key])
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
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

def fetch_star_data(star_id, config):
    """Fetch light curve data for a single star."""
    try:
        start_time = time.time()

        # Fetch the light curve data
        search_result = lk.search_lightcurvefile(star_id, mission='TESS')
        if len(search_result) == 0:
            logging.warning(f"No light curve data found for star_id: {star_id}")
            return None

        # Download the first light curve file from the search result
        lightcurve_file = search_result.download()

        # Define output and save path
        output_dir = config["raw_data_dir"]
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{star_id.replace(' ', '_')}.fits")

        # Save the downloaded fits file
        lightcurve_file.write(output_path, overwrite=True)

        elapsed_time = time.time() - start_time
        logging.debug(f"Successfully fetched data for {star_id} in {elapsed_time:.2f} seconds")
        return elapsed_time
    except Exception as e:
        logging.error(f"Failed to fetch data for star_id: {star_id}. Error: {str(e)}")
        return None

def load_star_ids(config):
    """Load star IDs from the input file."""
    try:
        with open(config["star_ids_file"], "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logging.error(f"The file {config['star_ids_file']} does not exist.")
        return None
    except Exception as e:
        logging.error(f"Error reading star IDs: {e}")
        return None
    
def trigger_next_module():
    """Trigger the next module in the pipeline if it exists."""
    try:
        config = load_config()
        project_root = get_project_root()
        relative_script_path = config.get("process_lightcurve_script")
        next_script = os.path.join(project_root, relative_script_path)

        logging.debug(f"Resolved path for process_lightcurve.py: {next_script}")

        if next_script and os.path.exists(next_script):
            logging.debug("Triggering process_lightcurve.py...")
            subprocess.run(["python", next_script], check=True)
            logging.debug("Successfully triggered process_lightcurve.py")
            return True
        else:
            logging.warning(f"Next module process_lightcurve.py not found at {next_script}")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running process_lightcurve.py: {e}")
        return False


def main():
    """Main function to process all stars and trigger next module."""
    try:
        config = load_config()
        if not config:
            return False

        if not setup_logging(config, "fetch_star_data_log"):
            return False

        # Load star IDs
        star_ids = load_star_ids(config)
        if not star_ids:
            return False

        logging.debug(f"Starting to process {len(star_ids)} stars...")

        # Process each star
        successful_fetches = 0
        for star_id in star_ids:
            logging.debug(f"Processing star_id: {star_id}")
            result = fetch_star_data(star_id, config)

            if result is not None:
                successful_fetches += 1
                logging.debug(f"Successfully processed {star_id}")
            else:
                logging.warning(f"Failed to process {star_id}")

        # Log summary
        logging.debug(f"Completed processing. Success rate: {successful_fetches}/{len(star_ids)}")

        # Try to trigger next module if any stars were processed successfully
        if successful_fetches > 0:
            trigger_next_module()
            return True
        else:
            logging.error("No stars were successfully processed")
            return False
    except Exception as e:
        logging.error(f"Unexpected error in main: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        logging.error("Pipeline execution failed")
        exit(1)
