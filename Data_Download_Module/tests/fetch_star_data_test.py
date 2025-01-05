from ..scripts.fetch_star_data import load_config, fetch_star_data


def test_insert_star_metadata():
    config = load_config()
    if not config:
        print("Configuration file not found!")
        return
    
    tic_id = "TIC_84326686"
    results = fetch_star_data(tic_id, config)
    if results:
        print("Star data fetched successfully.")
    else:
        print("Failed to fetch star data.")

if __name__ == "__main__":
    test_insert_star_metadata()

