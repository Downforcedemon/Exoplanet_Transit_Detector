from astroquery.mast import Catalogs
import os
import time
import logging
import json

# Define the configuration file path dynamically
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")

# Load configuration file
try:
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Configuration file not found at {CONFIG_PATH}. Exiting.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error parsing configuration file: {e}. Exiting.")
    exit(1)

# Extract parameters from config
OUTPUT_PATH = config["output_path"]
NUM_STARS_IDS = config["num_star_ids"]
CATALOG = config["catalog"]
QUERY_PARAMETERS = config["query_parameters"]
LOG_FILE = config["log_file"]

# Configure centralized logging
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
logging.debug(f"Loaded configuration: {config}")

# Query for stars
def query_star_catalog():
    """
    Query the MAST star catalog (e.g., TIC) for stars in the selected sector
    with optional filters like brightness.
    """
    try:
        logging.debug("Starting query...")
        start_time = time.time()  # Start the timer

        # Define the base query
        query_results = Catalogs.query_criteria(
            catalog=CATALOG,
            Tmag=(QUERY_PARAMETERS["brightness_range"][0], QUERY_PARAMETERS["brightness_range"][1])
        )

        # Calculate time taken
        query_duration = time.time() - start_time
        logging.debug(f"Query completed in {query_duration:.2f} seconds.")

        # Debug: Display a subset of the results
        if len(query_results) > 0:
            logging.debug(f"Sample of fetched star IDs: {query_results[:5]['ID']}")

        # Check if enough results were returned
        if len(query_results) < NUM_STARS_IDS:
            logging.warning(f"Warning: Only {len(query_results)} stars fetched (fewer than {NUM_STARS_IDS}).")
        else:
            logging.debug(f"Successfully fetched {len(query_results)} stars from {CATALOG}.")

        # Return the results as a table
        return query_results

    except Exception as e:
        logging.error(f"Error querying the star catalog: {e}")
        return None

# Save star IDs to text file
def save_star_ids(query_results):
    try:
        logging.debug("Saving star IDs to file...")
        with open(OUTPUT_PATH, "a") as file:
            for i, row in enumerate(query_results[:NUM_STARS_IDS]):
                file.write(f"TIC {row['ID']}\n")
                logging.debug(f"Saving star ID: TIC {row['ID']}")

        logging.debug(f"Successfully saved {NUM_STARS_IDS} star IDs to {OUTPUT_PATH}.")

    except Exception as e:
        logging.error(f"Error saving star IDs: {e}")

# Main function
if __name__ == "__main__":
    logging.debug("Fetching star IDs from MAST catalog...")
    results = query_star_catalog()

    if results is not None:
        logging.debug("Saving star IDs to file...")
        save_star_ids(results)
        logging.debug("Process complete.")
    else:
        logging.error("Error fetching star IDs. Process incomplete.")
