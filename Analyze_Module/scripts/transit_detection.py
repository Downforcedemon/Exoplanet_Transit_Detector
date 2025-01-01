import numpy as np
from astropy.timeseries import BoxLeastSquares
import logging
import json


def empty_results():
    """Return an empty result dictionary for failed detections."""
    return {"period": None, "duration": None, "depth": None, "power": None}


def run_bls(time, flux, flux_err, config):
    """Run the Box Least Squares (BLS) algorithm for transit detection."""
    try:
        # Log the start of the process
        logging.debug("Starting Box Least Squares (BLS) transit detection.")

        # Validate input arrays
        if len(time) == 0 or len(flux) == 0 or len(flux_err) == 0:
            logging.warning("Input arrays are empty. Skipping transit detection.")
            return empty_results()

        if len(time) != len(flux) or len(flux) != len(flux_err):
            logging.warning("Input arrays have inconsistent lengths. Skipping transit detection.")
            return empty_results()

        # Load the BLS parameters from config.json
        bls_parameters = config.get("bls_parameters", {})
        period_range = bls_parameters.get("period_range", [0.5, 30])
        duration_range = bls_parameters.get("duration_range", [0.01, 0.1])

        # Validate period range
        if period_range[0] >= period_range[1]:
            logging.error("Invalid period range: Start must be less than end.")
            return empty_results()

        # Log the BLS parameters
        logging.debug(f"BLS parameters: Period Range = {period_range}, Duration Range = {duration_range}")

        # Initialize the BLS model
        model = BoxLeastSquares(time, flux, flux_err)

        # Perform the BLS search
        results = model.autopower(duration_range)

        # Extract the best-fit results
        best_index = np.argmax(results.power)
        best_period = results.period[best_index]
        best_duration = results.duration[best_index]
        best_depth = results.depth[best_index]
        best_power = results.power[best_index]

        # Log the results
        logging.debug(f"BLS results: Period = {best_period}, Duration = {best_duration}, Depth = {best_depth}, Power = {best_power}")

        # Return the transit metrics
        return {
            "period": best_period,
            "duration": best_duration,
            "depth": best_depth,
            "power": best_power
        }

    except Exception as e:
        logging.error(f"Error during BLS transit detection: {e}")
        return empty_results()
