import os
import logging
import json
from minio import Minio
import cx_Oracle
from time import sleep
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Oracle Database configuration
ORACLE_DSN = os.getenv("ORACLE_DSN")
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")

# Minio configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET_PROCESSED = os.getenv("MINIO_BUCKET_PROCESSED")
MINIO_BUCKET_VISUALIZE = os.getenv("MINIO_BUCKET_VISUALIZE")

# Get TIC ID from command line argument
TIC_ID = sys.argv[1]

# Construct file paths
PROCESSED_PNG_PATH = f"Process_Light_Curve_Module/data/processed/{TIC_ID}_processed.png"
METRICS_PNG_PATH = f"visualize_transits_module/data/{TIC_ID}_processed_metrics.png"
RESULTS_JSON_PATH = f"Analyze_Module/results/{TIC_ID}_processed_results.json"
LOG_FILE_PATH = f"visualize_transits_module/logs/visualize_transits.log"

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH)
    ]
)
logging.info(f"Starting DB writer for TIC ID: {TIC_ID}")

def upload_to_minio(bucket_name, file_path, object_name):
    try:
        # Initialize MinIO client
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False  
        )

        # Check if the file exists
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return False

        # Upload the file to the specified bucket
        minio_client.fput_object(bucket_name, object_name, file_path)
        logging.info(f"Successfully uploaded {file_path} to {bucket_name}/{object_name}")
        return True
    except Exception as e:
        logging.error(f"Error uploading file {file_path} to MinIO: {e}")
        return False

def insert_results_into_oracle(star_id, result_data):
    try:
        # Establish Oracle database connection
        connection = cx_Oracle.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
            mode=cx_Oracle.SYSDBA
        )
        cursor = connection.cursor()

        # Insert results into analysis_results table
        insert_query = """
        INSERT INTO analysis_results (star_id, period, duration, depth, power, timestamp)
        VALUES (:star_id, :period, :duration, :depth, :power, SYSTIMESTAMP)
        """
        cursor.execute(insert_query, {
            "star_id": star_id,
            "period": result_data["period"],
            "duration": result_data["duration"],
            "depth": result_data["depth"],
            "power": result_data["power"]
        })

        # Commit the transaction
        connection.commit()
        logging.info(f"Successfully inserted results for star_id: {star_id}")
        return True
    except Exception as e:
        logging.error(f"Error inserting results for star_id {star_id}: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def main():
    try:
        logging.info("Starting the db_writer workflow...")

        # Validate file existence
        if not os.path.exists(PROCESSED_PNG_PATH):
            logging.error(f"Processed PNG file not found: {PROCESSED_PNG_PATH}")
            return
        if not os.path.exists(METRICS_PNG_PATH):
            logging.error(f"Metrics PNG file not found: {METRICS_PNG_PATH}")
            return
        if not os.path.exists(RESULTS_JSON_PATH):
            logging.error(f"Results JSON file not found: {RESULTS_JSON_PATH}")
            return

        # Upload files to MinIO
        upload_to_minio(
            bucket_name=MINIO_BUCKET_PROCESSED,
            file_path=PROCESSED_PNG_PATH,
            object_name=f"{TIC_ID}_processed.png"
        )

        upload_to_minio(
            bucket_name=MINIO_BUCKET_VISUALIZE,
            file_path=METRICS_PNG_PATH,
            object_name=f"{TIC_ID}_processed_metrics.png"
        )

        # Insert results into Oracle Database
        with open(RESULTS_JSON_PATH, 'r') as json_file:
            result_data = json.load(json_file)
            insert_results_into_oracle(TIC_ID, result_data)

        logging.info("db_writer workflow completed successfully.")

    except Exception as e:
        logging.error(f"Unexpected error in db_writer workflow: {e}")

if __name__ == "__main__":
    main()



