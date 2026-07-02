import json
import time
import uuid
import random
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Import Enums from domain module
from sensor import QualityFlag, StationID, SensorID, DeviceID, SensorType, SENSOR_TYPE_MAP, SENSOR_METRICS_MAP

# Load environment variables from .env file
load_dotenv()

# Google Cloud Pub/Sub Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
TOPIC_ID = os.getenv("GCP_TOPIC_ID", "digital_twin")
CREDENTIALS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# Flag to check if Pub/Sub client can be initialized
publisher = None
topic_path = None

if CREDENTIALS_FILE and os.path.exists(CREDENTIALS_FILE):
    try:
        from google.cloud import pubsub_v1
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
        print(f"[INFO] Initialized Google Cloud Pub/Sub Client for topic: {topic_path}")
    except Exception as e:
        print(f"[WARN] Could not initialize Pub/Sub Client: {e}")
else:
    print("[INFO] Running in SIMULATION ONLY mode (No valid GOOGLE_APPLICATION_CREDENTIALS found).")

def generate_sensor_data():
    """Generates realistic simulated IoT water quality sensor data with randomized Enums."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Randomly select Enums
    station = random.choice(list(StationID))
    sensor = random.choice(list(SensorID))
    device = random.choice(list(DeviceID))
    quality = random.choices(
        list(QualityFlag), 
        weights=[0.85, 0.08, 0.04, 0.02, 0.01]
    )[0]
    
    sensor_type = SENSOR_TYPE_MAP.get(sensor, SensorType.MULTI_PARAMETER)
    active_metrics = SENSOR_METRICS_MAP.get(sensor_type, [])
    
    # Available metric values pool
    all_possible_values = {
        "pH": round(random.uniform(6.8, 8.2), 2),
        "dissolved_oxygen_mg_l": round(random.uniform(5.5, 8.5), 2),
        "temperature_c": round(random.uniform(25.0, 32.0), 1),
        "turbidity_ntu": round(random.uniform(5.0, 25.0), 1),
        "electrical_conductivity_us_cm": round(random.uniform(700.0, 950.0), 1),
        "orp_mv": round(random.uniform(200.0, 300.0), 1),
        "water_level_m": round(random.uniform(1.2, 2.5), 2),
    }
    if "electrical_conductivity_us_cm" in all_possible_values:
        all_possible_values["tds_mg_l"] = round(all_possible_values["electrical_conductivity_us_cm"] * 0.5, 1)

    # Base payload structure
    payload = {
        "observation_id": str(uuid.uuid4()),
        "timestamp": now,
        "station_id": station.value,
        "sensor_id": sensor.value,
        "sensor_type": sensor_type.value,
        "battery_voltage": round(random.uniform(3.6, 4.2), 2),
        "quality_flag": quality.value,
        "raw_payload": {
            "dev_id": device.value,
            "rssi": random.randint(-85, -60)
        }
    }

    # Dynamically populate measured metrics defined by the sensor type
    for metric in active_metrics:
        if metric in all_possible_values:
            payload[metric] = all_possible_values[metric]
            
    return payload

def main():
    interval_seconds = int(os.getenv("PUBLISH_INTERVAL_SECONDS", "5"))
    print(f"[START] Starting IoT Sensor Simulator with Enums (Interval: {interval_seconds}s)... Press Ctrl+C to stop.\n")
    
    try:
        while True:
            data = generate_sensor_data()
            data_bytes = json.dumps(data, indent=2).encode("utf-8")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Telemetry from {data['station_id']} ({data['raw_payload']['dev_id']}):")
            print(json.dumps(data, indent=2))
            
            if publisher and topic_path:
                try:
                    future = publisher.publish(topic_path, data_bytes)
                    message_id = future.result()
                    print(f"-> Published to Pub/Sub! Message ID: {message_id}\n")
                except Exception as pub_err:
                    print(f"-> [ERROR] Failed to publish to Pub/Sub: {pub_err}\n")
            else:
                print("-> [DRY RUN] Skipped sending to GCP Pub/Sub.\n")
                
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n[STOP] Simulator stopped by user.")

if __name__ == "__main__":
    main()
