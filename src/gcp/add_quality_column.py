import os
import sys

# Add project root to python path
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(src_dir)
sys.path.append(project_root)

from google.cloud import bigquery
from src.gcp.client import gcp_client

def add_column():
    if not gcp_client.credentials:
        print("Error: GCP Credentials not loaded.")
        sys.exit(1)

    client = bigquery.Client(
        project=gcp_client.project_id,
        credentials=gcp_client.credentials
    )

    table_id = f"{gcp_client.project_id}.test.device_telemetry"
    print(f"Adding quality_flag column to table: {table_id}")
    try:
        table = client.get_table(table_id)
        # Check if quality_flag already exists
        if any(field.name == "quality_flag" for field in table.schema):
            print("quality_flag already exists.")
            return

        schema = table.schema
        new_schema = list(schema)
        new_schema.append(bigquery.SchemaField("quality_flag", "STRING", mode="NULLABLE"))
        table.schema = new_schema
        client.update_table(table, ["schema"])
        print("Successfully added quality_flag column.")
    except Exception as e:
        print(f"Failed to add column: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_column()
