import os
import logging
import json
import numpy as np
from astropy.io import fits
from datetime import datetime
from transit_detection import run_bls  
from db_writer import save_results  
from trigger_visualize import notify_success  

def load_config():
    """Load the configuration from the config.json file."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.error("Config file not found.")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing config file: {e}")
        return None

def setup_logging(log_file):
    """Set up logging configuration."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def analyze_transit(file_path, output_dir):
    """Analyze a single processed FITS file for potential transits."""
    try:
        # Verify the file exists
        if not os.path.exists(file_path):
            logging.error(f"Processed FITS file not found: {file_path}")
            return False

        # Load the processed FITS file
        with fits.open(file_path) as hdul:
            data = hdul[1].data
            time = data["TIME"]
            flux = data["PDCSAP_FLUX"]
            flux_err = data["PDCSAP_FLUX_ERR"]

        # Validate data
        valid = ~np.isnan(time) & ~np.isnan(flux)
        time = time[valid]
        flux = flux[valid]
        flux_err = flux_err[valid]
        if len(time) < 10:  # Minimum data points required
            logging.warning(f"Insufficient valid data in {file_path}. Skipping analysis.")
            return False

        # Perform transit detection
        logging.debug(f"Running transit detection on {file_path}")
        transit_results = run_bls(time, flux, flux_err)

        # Save results to a temporary JSON file
        results_path = os.path.join(output_dir, os.path.basename(file_path).replace('.fits', '_results.json'))
        with open(results_path, 'w') as f:
            json.dump(transit_results, f, indent=4)
        logging.debug(f"Saved transit detection results to {results_path}")

        # Save results to the database
        save_results(transit_results)
        logging.debug("Transit detection results saved to the database.")

        # Trigger visualization
        notify_success(file_path)
        logging.debug("Visualization module successfully triggered.")

        return True

    except Exception as e:
        logging.error(f"Error analyzing FITS file {file_path}: {e}")
        return False

if __name__ == "__main__":
    # Load configuration
    config = load_config()
    if not config:
        exit(1)

    # Set up logging
    log_file = config["analyze_transits"]["log_file"]
    setup_logging(log_file)

    # Read file path and output directory from configuration
    processed_fits_path = config["analyze_transits"]["processed_fits_path"]
    output_dir = config["analyze_transits"]["output_dir"]

    # Log the start of the analysis
    logging.debug(f"Starting transit analysis for file: {processed_fits_path}")

    # Run the transit analysis
    success = analyze_transit(processed_fits_path, output_dir)

    # Log the completion of the analysis
    if success:
        logging.debug("Transit analysis completed successfully.")
    else:
        logging.error("Transit analysis failed.")


