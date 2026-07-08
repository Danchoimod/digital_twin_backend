import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud import bigquery

from src.auth.dependencies import get_current_user
from src.gcp.client import gcp_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telemetry", tags=["telemetry"])

@router.get("/historical")
async def get_historical_telemetry(
    limit: int = 30,
    current_user=Depends(get_current_user)
):
    """
    Query historical sensor telemetry data from Google Cloud BigQuery.
    """
    if not gcp_client.credentials:
        logger.warning("GCP Credentials not loaded. Returning empty telemetry.")
        return []

    try:
        # Initialize BigQuery client with loaded credentials
        client = bigquery.Client(
            project=gcp_client.project_id,
            credentials=gcp_client.credentials
        )
        
        # SQL query to get recent device telemetry
        # Dataset name is 'test' and Table name is 'device_telemetry'
        query_string = f"""
            SELECT observation_id, timestamp, station_id, sensor_type, metrics
            FROM `{gcp_client.project_id}.test.device_telemetry`
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        
        logger.info(f"Running BigQuery query: {query_string}")
        query_job = client.query(query_string)
        results = query_job.result()
        
        telemetry_data = []
        for row in results:
            # Parse the metrics JSON or dict
            parsed_metrics = {}
            if row.metrics:
                if isinstance(row.metrics, dict):
                    parsed_metrics = row.metrics
                elif isinstance(row.metrics, str):
                    try:
                        parsed_metrics = json.loads(row.metrics)
                    except Exception as e:
                        logger.error(f"Error parsing metrics JSON for row {row.observation_id}: {e}")
                else:
                    # Fallback or other formats
                    parsed_metrics = row.metrics
                    
            telemetry_data.append({
                "observation_id": row.observation_id,
                "timestamp": row.timestamp,
                "station_id": row.station_id,
                "sensor_type": row.sensor_type,
                "metrics": parsed_metrics
            })
            
        # Reverse list to return chronological order (oldest to newest for charting)
        telemetry_data.reverse()
        return telemetry_data

    except Exception as e:
        logger.error(f"Failed to query BigQuery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch historical telemetry: {str(e)}"
        )
