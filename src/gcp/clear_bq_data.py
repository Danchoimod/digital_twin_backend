import os
import sys

# Add project root to python path
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(src_dir)
sys.path.append(project_root)

from google.cloud import bigquery
from src.gcp.client import gcp_client

def clear_data():
    if not gcp_client.credentials:
        print("Error: GCP Credentials not loaded.")
        sys.exit(1)

    client = bigquery.Client(
        project=gcp_client.project_id,
        credentials=gcp_client.credentials
    )

    # 1. Recreate device_telemetry
    main_table_id = f"{gcp_client.project_id}.test.device_telemetry"
    print(f"Deleting table if exists: {main_table_id}")
    client.delete_table(main_table_id, not_found_ok=True)
    
    main_schema = [
        bigquery.SchemaField("observation_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("station_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("sensor_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("metrics", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("raw_payload", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("quality_flag", "STRING", mode="NULLABLE")
    ]
    main_table = bigquery.Table(main_table_id, schema=main_schema)
    print(f"Recreating table: {main_table_id}")
    client.create_table(main_table)
    print(f"Successfully recreated table: {main_table_id}")

    # 2. Recreate device_telemetry_dead_letter
    dlq_table_id = f"{gcp_client.project_id}.test.device_telemetry_dead_letter"
    print(f"Deleting table if exists: {dlq_table_id}")
    client.delete_table(dlq_table_id, not_found_ok=True)
    
    dlq_schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("raw_payload", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("error_reason", "STRING", mode="NULLABLE")
    ]
    dlq_table = bigquery.Table(dlq_table_id, schema=dlq_schema)
    print(f"Recreating table: {dlq_table_id}")
    client.create_table(dlq_table)
    print(f"Successfully recreated table: {dlq_table_id}")

if __name__ == "__main__":
    clear_data()
