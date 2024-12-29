from astropy.io import fits

with fits.open("/home/sm/Projects/Exoplanet_Transit_Detector/Data_Download_Module/data/raw/TIC_269400564.fits") as hdul:
    print(hdul.info())
    print(hdul[0].header)
    print(hdul[1].columns)
    print(hdul[1].data[:5])

