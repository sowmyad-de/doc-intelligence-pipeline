"""
Snowflake Bronze Loader
Reads 500 extracted JSON files and loads them into BRONZE_CLAIMS_RAW.
"""

import os
import glob
import time
from pathlib import Path
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

JSON_DIR = Path.home() / "Desktop" / "doc-intelligence-pipeline" / "data" / "extracted_json"
STAGE_NAME = "RAW_JSON_STAGE"
TABLE_NAME = "BRONZE_CLAIMS_RAW"


def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def upload_files_to_stage(cursor, json_dir):
    json_files = sorted(glob.glob(str(json_dir / "*.json")))
    total = len(json_files)
    print(f"Found {total} JSON files to upload")

    if total == 0:
        raise FileNotFoundError(f"No JSON files found in {json_dir}")

    put_command = f"PUT 'file://{json_dir}/*.json' @{STAGE_NAME} AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
    print(f"\nRunning PUT command...")
    start = time.time()
    cursor.execute(put_command)
    results = cursor.fetchall()
    elapsed = time.time() - start

    uploaded = sum(1 for r in results if r[6] == "UPLOADED")
    skipped = sum(1 for r in results if r[6] == "SKIPPED")
    print(f"Uploaded: {uploaded} | Skipped: {skipped} | Time: {elapsed:.1f}s")
    return uploaded


def copy_into_bronze(cursor):
    print("\nTruncating BRONZE_CLAIMS_RAW for clean load...")
    cursor.execute(f"TRUNCATE TABLE {TABLE_NAME}")

    copy_sql = f"""
        COPY INTO {TABLE_NAME} (FILE_NAME, RAW_JSON)
        FROM (
            SELECT
                METADATA$FILENAME,
                $1
            FROM @{STAGE_NAME}
        )
        FILE_FORMAT = (TYPE = JSON)
        ON_ERROR = 'CONTINUE'
    """
    print("Running COPY INTO...")
    start = time.time()
    cursor.execute(copy_sql)
    results = cursor.fetchall()
    elapsed = time.time() - start

    total_loaded = sum(r[2] for r in results)
    total_failed = sum(r[3] for r in results)
    print(f"Loaded: {total_loaded} rows | Failed: {total_failed} rows | Time: {elapsed:.1f}s")
    return total_loaded


def verify_load(cursor):
    print("\n--- Verification ---")

    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    row_count = cursor.fetchone()[0]
    print(f"Total rows in BRONZE_CLAIMS_RAW: {row_count}")

    cursor.execute(f"SELECT FILE_NAME, INGESTED_AT FROM {TABLE_NAME} LIMIT 3")
    print("\nSample rows:")
    for row in cursor.fetchall():
        print(f"  {row[0]}  |  ingested at {row[1]}")


def main():
    print(f"Source directory: {JSON_DIR}\n")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        upload_files_to_stage(cursor, JSON_DIR)
        copy_into_bronze(cursor)
        verify_load(cursor)
        print("\nBronze load complete.")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()