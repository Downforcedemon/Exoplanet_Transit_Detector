import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

file_path = "/home/sm/Projects/Exoplanet_Transit_Detector/Data_Download_Module/data/raw/TIC_269400564.fits"

try:
    with fits.open(file_path) as hdul:
        # Access the binary table HDU
        data = hdul[1].data

        # Extract the columns
        time = data["time"]  # Time column
        flux = data["pdcsap_flux"]  # Detrended flux column
        flux_err = data["pdcsap_flux_err"]  # Flux error column

        # Flatten the time column if it has an extra dimension
        if len(time.shape) > 1:
            time = time[:, 0]  # Select the first dimension

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

        # Save the plot as an image
        plot_path = "extracted_light_curve.png"
        plt.savefig(plot_path)
        print(f"Saved the extracted light curve plot as '{plot_path}'.")

except Exception as e:
    print(f"Error processing FITS file: {e}")
