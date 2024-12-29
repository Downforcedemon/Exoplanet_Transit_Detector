import numpy as np
from astropy.timeseries import BoxLeastSquares
import logging

def run_bls(time, flux, flux_err):
    """Run the Box Least Squares (BLS) algorithm for transit detection."""
    try:
        # Log the start of the process
        logging.debug("Starting Box Least Squares (BLS) transit detection.")

        # Validate input arrays
        if len(time) == 0 or len(flux) == 0 or len(flux_err) == 0:
            logging.warning("Input arrays are empty. Skipping transit detection.")
            return {}

        if len(time) != len(flux) or len(flux) != len(flux_err):
            logging.warning("Input arrays have inconsistent lengths. Skipping transit detection.")
            return {}

        # Initialize the BLS model
        model = BoxLeastSquares(time, flux, flux_err)

        # Define the period range and duration range
        period_range = (0.5, 30)  # Search for periods between 0.5 and 30 days
        duration_range = (0.01, 0.1)  # Search for durations as a fraction of the period

        # Perform the BLS search
        results = model.autopower(duration_range)

        # Extract the best-fit results
        best_period = results.period[np.argmax(results.power)]
        best_duration = results.duration[np.argmax(results.power)]
        best_depth = results.depth[np.argmax(results.power)]

        # Log the results
        logging.debug(f"BLS results: Period = {best_period}, Duration = {best_duration}, Depth = {best_depth}")

        # Return the transit metrics
        return {
            "period": best_period,
            "duration": best_duration,
            "depth": best_depth,
            "power": np.max(results.power)
        }

    except Exception as e:
        logging.error(f"Error during BLS transit detection: {e}")
        return {}

