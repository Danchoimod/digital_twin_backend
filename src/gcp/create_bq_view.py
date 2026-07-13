import os
import sys

# Add project root to python path
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(src_dir)
sys.path.append(project_root)

from google.cloud import bigquery
from src.gcp.client import gcp_client

def create_view():
    if not gcp_client.credentials:
        print("Error: GCP Credentials not loaded.")
        sys.exit(1)

    client = bigquery.Client(
        project=gcp_client.project_id,
        credentials=gcp_client.credentials
    )

    view_id = f"{gcp_client.project_id}.test.vw_water_quality_telemetry"
    
    # BigQuery DDL for view creation
    # Safely extract metrics values from the JSON field
    sql = f"""
    CREATE OR REPLACE VIEW `{view_id}` AS
    SELECT
      observation_id,
      timestamp,
      station_id,
      sensor_type,
      quality_flag,
      SAFE_CAST(JSON_VALUE(metrics, '$.ph') AS FLOAT64) AS ph,
      SAFE_CAST(JSON_VALUE(metrics, '$.temperature') AS FLOAT64) AS temperature_c,
      SAFE_CAST(JSON_VALUE(metrics, '$.dissolved_oxygen') AS FLOAT64) AS dissolved_oxygen_mg_l,
      SAFE_CAST(JSON_VALUE(metrics, '$.turbidity') AS FLOAT64) AS turbidity_ntu,
      SAFE_CAST(JSON_VALUE(metrics, '$.electrical_conductivity') AS FLOAT64) AS electrical_conductivity_us_cm,
      SAFE_CAST(JSON_VALUE(metrics, '$.tds') AS FLOAT64) AS tds_mg_l,
      SAFE_CAST(JSON_VALUE(metrics, '$.orp') AS FLOAT64) AS orp_mv,
      SAFE_CAST(JSON_VALUE(metrics, '$.water_level') AS FLOAT64) AS water_level_m,
      SAFE_CAST(JSON_VALUE(raw_payload, '$.rssi') AS INT64) AS rssi
    FROM
      `{gcp_client.project_id}.test.device_telemetry`
    """
    
    print(f"Creating/updating BigQuery View: {view_id}")
    try:
        query_job = client.query(sql)
        query_job.result()  # Wait for query to complete
        print(f"Successfully created view: {view_id}")
    except Exception as e:
        print(f"Failed to create view: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_view()
