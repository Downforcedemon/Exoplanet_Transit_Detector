import time
import os
import lightkurve as lk
import logging
import subprocess
import json
import warnings
from datetime import datetime
import cx_Oracle  # For database operations

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
        os.makedirs(os.path.dirname(config[log_key]), exist_ok=True)
        file_handler = logging.FileHandler(config[log_key])
        console_handler = logging.StreamHandler()
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logging.captureWarnings(True)
        warnings.simplefilter("ignore")  # Suppress non-critical warnings
        logging.debug("Logging setup complete.")
        return True
    except Exception as e:
        print(f"Error setting up logging: {e}")
        return False

def fetch_star_data(star_id, config):
    """Fetch light curve data for a single star and insert metadata."""
    try:
        start_time = time.time()

        # Fetch the light curve data
        search_result = lk.search_lightcurve(star_id, mission='TESS')
        if len(search_result) == 0:
            logging.warning(f"No light curve data found for star_id: {star_id}")
            return None

        # Download the first light curve file from the search result
        lightcurve = search_result.download()

        # Define output and save path
        output_dir = config["raw_data_dir"]
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{star_id.replace(' ', '_')}.fits")

        # Save the light curve to FITS
        if hasattr(lightcurve, "hdu"):
            lightcurve.hdu.writeto(output_path, overwrite=True)
        else:
            logging.error(f"Cannot save light curve for {star_id}: Missing HDU attribute.")
            return None

        # Insert star metadata into the database
        brightness = lightcurve.meta.get("PHOTONS", 0.0)  # Example brightness extraction
        catalog = "TESS"
        observation_time = datetime.now()

        insert_star_metadata(
            star_id=star_id,
            name=lightcurve.meta.get("OBJECT", "Unknown"),  # Star name from metadata
            brightness=brightness,
            catalog=catalog,
            observation_time=observation_time
        )

        elapsed_time = time.time() - start_time
        logging.debug(f"Successfully fetched data for {star_id} in {elapsed_time:.2f} seconds")
        return elapsed_time
    except Exception as e:
        logging.error(f"Failed to fetch data for star_id: {star_id}. Error: {str(e)}")
        return None

def insert_star_metadata(star_id, name, brightness, catalog, observation_time=None):
    try:
        connection = cx_Oracle.connect(
            user=os.getenv("ORACLE_USER"),
            password=os.getenv("ORACLE_PASSWORD"),
            dsn=os.getenv("ORACLE_DSN")
        )
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM star_metadata WHERE star_id = :star_id", {"star_id": star_id})
        exists = cursor.fetchone()[0]

        if not exists:
            cursor.execute("""
                INSERT INTO star_metadata (star_id, name, brightness, observation_time, catalog)
                VALUES (:star_id, :name, :brightness, :observation_time, :catalog)
            """, {
                "star_id": star_id,
                "name": name or "Unknown",
                "brightness": brightness or 0.0,
                "observation_time": observation_time or "SYSDATE",
                "catalog": catalog or "Unknown"
            })
            connection.commit()
            logging.info(f"Inserted metadata for star_id: {star_id}")
    except Exception as e:
        logging.error(f"Error inserting star metadata for star_id {star_id}: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def load_star_ids(config):
    """Load star IDs from the input file."""
    try:
        with open(config["star_ids_file"], "r") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        logging.error(f"Error loading star IDs: {e}")
        return None

def trigger_next_module():
    """Trigger the next module in the pipeline if it exists."""
    try:
        config = load_config()
        next_script = os.path.join(get_project_root(), config.get("process_lightcurve_script", ""))
        if os.path.exists(next_script):
            subprocess.run(["python", next_script], check=True)
            logging.debug("Successfully triggered process_lightcurve.py")
            return True
        else:
            logging.warning(f"process_lightcurve.py not found at {next_script}")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error triggering process_lightcurve.py: {e}")
        return False

def main():
    """Main function to process all stars and trigger next module."""
    try:
        config = load_config()
        if not config:
            return False

        if not setup_logging(config, "fetch_star_data_log"):
            return False

        star_ids = load_star_ids(config)
        if not star_ids:
            return False

        successful_fetches = 0
        for star_id in star_ids:
            result = fetch_star_data(star_id, config)
            if result:
                successful_fetches += 1

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
