import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from datetime import datetime
import subprocess

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
    try:
        with fits.open(file_path) as hdul:
            # Access the binary table HDU
            data = hdul[1].data
            header = hdul[1].header

            # Extract columns
            time = data["time"]
            flux = data["pdcsap_flux"]
            flux_err = data["pdcsap_flux_err"]

            # Log shapes for debugging
            logging.debug(f"Initial shapes - Time: {time.shape}, Flux: {flux.shape}, Flux Err: {flux_err.shape}")

            # Ensure arrays are 1D by flattening if necessary
            if len(time.shape) > 1:
                time = time[:, 0]  # Select the first column
            if len(flux.shape) > 1:
                flux = flux[:, 0]
            if len(flux_err.shape) > 1:
                flux_err = flux_err[:, 0]

            # Log shapes after flattening
            logging.debug(f"Flattened shapes - Time: {time.shape}, Flux: {flux.shape}, Flux Err: {flux_err.shape}")

            # Clean the data
            valid = ~np.isnan(flux) & ~np.isnan(time)
            time = time[valid]
            flux = flux[valid]
            flux_err = flux_err[valid]

            # Plot and save PNG (existing logic)
            plot_path = os.path.join(output_dir, os.path.basename(file_path).replace('.fits', '_processed.png'))
            plt.plot(time, flux, ".-", label="PDCSAP Flux")
            plt.xlabel("Time (days)")
            plt.ylabel("Flux")
            plt.legend()
            plt.savefig(plot_path)
            logging.debug(f"Saved light curve plot as {plot_path}")

            # Save processed data as a new .fits file
            processed_fits_path = os.path.join(output_dir, os.path.basename(file_path).replace('.fits', '_processed.fits'))
            save_processed_fits(time, flux, flux_err, header, processed_fits_path)
            logging.debug(f"Saved processed FITS file as {processed_fits_path}")

            # Trigger Analyze Module
            success = trigger_analyze_transits(processed_fits_path)
            if not success:
                logging.error(f"Error triggering Analyze Module for {processed_fits_path}")

            return True

    except Exception as e:
        logging.error(f"Error processing light curve {file_path}: {e}")
        return False


def save_processed_fits(time, flux, flux_err, header, output_path):
    try:
        # Define new columns for FITS file
        cols = fits.ColDefs([
            fits.Column(name='TIME', format='D', array=time),
            fits.Column(name='PDCSAP_FLUX', format='E', array=flux),
            fits.Column(name='PDCSAP_FLUX_ERR', format='E', array=flux_err)
        ])

        # Create a new binary table HDU
        hdu = fits.BinTableHDU.from_columns(cols)
        hdu.header = header

        # Add custom metadata
        hdu.header['PREPROC'] = "Flattened, Cleaned, Masked NaNs"
        hdu.header['COMMENT'] = "Processed by Process Light Curve Module"
        hdu.header['DATEPROC'] = datetime.now().isoformat()

        # Write to output file
        hdu.writeto(output_path, overwrite=True)
    except Exception as e:
        logging.error(f"Error saving processed FITS file: {e}")

def process_all_lightcurves(raw_data_dir, processed_data_dir):
    try:
        success_count = 0  # Initialize counters
        failure_count = 0

        for file_name in os.listdir(raw_data_dir):
            file_path = os.path.join(raw_data_dir, file_name)
            if file_name.endswith(".fits"):
                logging.debug(f"Processing file: {file_path}")
                success = process_lightcurve(file_path, processed_data_dir)
                if success:
                    logging.debug(f"Successfully processed: {file_path}")
                    success_count += 1
                else:
                    logging.warning(f"Failed to process: {file_path}")
                    failure_count += 1

        # Return a summary of results
        return {"success": success_count, "failure": failure_count}

    except Exception as e:
        logging.error(f"Error processing light curves in {raw_data_dir}: {e}")
        return {"success": 0, "failure": 0}  # Return default values in case of error
    
# trigger  next module --> analysis
def trigger_analyze_transits(processed_fits_path): 
    try:
        # path to analyze_transits.py
        analyze_script_path = "Analyze_Module/scripts/analyze_transits.py"
        if not os.path.exists(analyze_script_path):
            logging.error(f"Analyze script not found at {analyze_script_path}")
            return False
        
        # trigger analyze_transits.py
        logging.debug(f"Triggering Analyze Module for file: {processed_fits_path}")
        result = subprocess.run(
            ["python",analyze_script_path, processed_fits_path],
            check=True,
            capture_output=True,
            text=True
        )
        logging.debug(f"Analyze Module ouput: {result.stdout}")
        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Error triggering Analyze Module: {e}")
        return False


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

    
