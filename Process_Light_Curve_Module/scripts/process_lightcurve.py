import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

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

def process_lightcurve(file_path, output_dir):
    """Process a single light curve file."""
    try:
        with fits.open(file_path) as hdul:
            # Access the binary table HDU
            data = hdul[1].data

            # Extract the columns
            time = data["time"]
            flux = data["pdcsap_flux"]
            flux_err = data["pdcsap_flux_err"]

            # Flatten the time column if it has an extra dimension
            if len(time.shape) > 1:
                time = time[:, 0]

            # Mask invalid (NaN) data
            valid = ~np.isnan(flux) & ~np.isnan(time)
            if valid.sum() == 0:
                raise ValueError("No valid data points found.")

            # Apply the mask
            time = time[valid]
            flux = flux[valid]
            flux_err = flux_err[valid]

            # Plot the extracted light curve
            plt.figure(figsize=(10, 5))
            plt.plot(time, flux, ".-", label="PDCSAP Flux")
            plt.xlabel("Time (days)")
            plt.ylabel("Flux")
            plt.title("Extracted Light Curve")
            plt.legend()

            # Define output and save path
            os.makedirs(output_dir, exist_ok=True)
            plot_path = os.path.join(output_dir, os.path.basename(file_path).replace('.fits', '_processed.png'))
            plt.savefig(plot_path)
            logging.debug(f"Saved the extracted light curve plot as '{plot_path}'.")

            return True

    except Exception as e:
        logging.error(f"Error processing light curve {file_path}: {e}")
        return False

def process_all_lightcurves(raw_data_dir, processed_data_dir):
    """Process all light curve files in the raw data directory."""
    try:
        for file_name in os.listdir(raw_data_dir):
            file_path = os.path.join(raw_data_dir, file_name)

            if file_name.endswith(".fits"):
                logging.debug(f"Processing file: {file_path}")
                success = process_lightcurve(file_path, processed_data_dir)

                if success:
                    logging.debug(f"Successfully processed: {file_path}")
                else:
                    logging.warning(f"Failed to process: {file_path}")
            else:
                logging.debug(f"Skipping non-FITS file: {file_name}")
    except Exception as e:
        logging.error(f"Error processing light curves in {raw_data_dir}: {e}")

def main():
    """Main function to load configuration, set up logging, and process light curves."""
    config = load_config()
    if not config:
        return

    log_file = config["process_lightcurve"]["process_lightcurve_log"]
    setup_logging(log_file)

    raw_data_dir = config["raw_data_dir"]
    processed_data_dir = config["process_lightcurve"]["processed_data_dir"]

    logging.debug("Starting light curve processing pipeline...")
    process_all_lightcurves(raw_data_dir, processed_data_dir)
    logging.debug("Light curve processing pipeline completed.")

if __name__ == "__main__":
    main()
