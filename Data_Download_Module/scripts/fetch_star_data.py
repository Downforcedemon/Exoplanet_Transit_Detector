import time
import os
import lightkurve as lk
import logging


def setup_logging():
    """
    Sets up the logging configuration for the single_star.py script.
    Logs will be written to data/logs/single_star.log.
    """

    # Configure logging settings
    logging.basicConfig(
        filename="data/logs/fetch_star_data.log",   # Log file path
        filemode="a",                          # Append mode; keeps existing logs and adds new entries
        format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
        level=logging.DEBUG                     # Logging level set to INFO
    )

    # Add a console handler for logging to the terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)    # Same level as file logging
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    # Attach the console handler to the root logger
    logging.getLogger().addHandler(console_handler)

    logging.info("Logging setup complete. Logs will be written to data/logs/fetch_star_data.log")

def fetch_star_data(star_id):
    try:
        start_time = time.time()       # start the timer
        #Fetch the light curve data
        search_result = lk.search_lightcurvefile(star_id,mission='Tess')
        if len(search_result) == 0:
            logging.warning(f"No light curve daa found for the star_id: {star_id}")
            return None
        
        # Download the first ligth curve file from the search result
        lightcurve_file = search_result.download()

        #Define output and save path
        output_dir = "data/raw/"
        output_path = os.path.join(output_dir, f"{star_id.replace(' ', '_')}.fits")

        # save the downloaded fits file
        lightcurve_file.write(output_path, overwrite=True)

        elapsed_time = time.time() - start_time     # calculate elapsed time
        logging.info(f"Successfully fetched data for {star_id} in {elapsed_time:.2f} seconds")
        return elapsed_time
    
    except Exception as e:
        logging.error(f"Failed to fetch data for star_id: {star_id}. Error: {str(e)}")
        return None
    
def main():
    """
    Main function to test fetching data for a single star.
    """
    # Set up logging
    setup_logging()

    # Load star IDs from inputs/star_ids.txt
    try:
        with open("inputs/star_ids.txt", "r") as file:
            star_ids = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logging.error("The file inputs/star_ids.txt does not exist. Please provide a valid file.")
        return

    # Test fetching data for the first star in the list
    if not star_ids:
        logging.warning("The file inputs/star_ids.txt is empty. No star IDs to fetch.")
        return

    logging.info("Starting single-star fetch test...")
    for star_id in star_ids[:1]:  # Only fetch for the first star in the list
        logging.info(f"Fetching data for star_id: {star_id}")
        time_taken = fetch_star_data(star_id)
        if time_taken is not None:
            logging.info(f"Success: Fetched data for {star_id} in {time_taken:.2f} seconds")
        else:
            logging.error(f"Failed to fetch data for {star_id}")

# Entry point for the script
if __name__ == "__main__":
    main()