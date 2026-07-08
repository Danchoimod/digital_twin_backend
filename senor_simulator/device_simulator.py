import os
import json
import time
import random
import logging
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Configure premium logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DeviceSimulator")

# Load environment configuration
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/data/phupham")
MQTT_KEEP_ALIVE = int(os.getenv("MQTT_KEEP_ALIVE", "60"))

DEVICE_ID = os.getenv("DEVICE_ID", "DEVICE_PHU_PHAM_001")
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "secret_token_123")
SEND_INTERVAL = float(os.getenv("SEND_INTERVAL_SECONDS", "5"))

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Successfully connected to MQTT Broker ({MQTT_BROKER}:{MQTT_PORT})")
    else:
        logger.error(f"Connection failed to MQTT Broker with code: {rc}")

def on_publish(client, userdata, mid):
    # Callback when publish completes
    pass

def main():
    logger.info("Initializing IoT Device Simulator...")
    logger.info(f"Device configuration: ID={DEVICE_ID}, Topic={MQTT_TOPIC}")

    client = mqtt.Client(client_id=f"{DEVICE_ID}_client")
    client.on_connect = on_connect
    client.on_publish = on_publish

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEP_ALIVE)
    except Exception as e:
        logger.error(f"Could not connect to broker: {e}")
        return

    # Start network loop in a background thread to handle reconnects
    client.loop_start()

    logger.info("Starting simulation loop. Press Ctrl+C to terminate.")

    try:
        while True:
            # Generate premium, realistic sensor telemetry data matching target BigQuery schema
            payload = {
                "observation_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "station_id": DEVICE_ID,
                "sensor_type": "water_quality",
                "metrics": {
                    "temperature_c": round(random.uniform(20.0, 35.0), 2),
                    "pH": round(random.uniform(6.5, 8.5), 2)
                },
                "raw_payload": {
                    "device_id": DEVICE_ID,
                    "token": DEVICE_TOKEN,
                    "rssi": -72
                }
            }

            payload_json = json.dumps(payload)
            # Publish to MQTT Broker
            result = client.publish(MQTT_TOPIC, payload_json)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published telemetry -> Observation: {payload['observation_id']}, Temp: {payload['metrics']['temperature_c']}°C, pH: {payload['metrics']['pH']}")
            else:
                logger.warning(f"Failed to publish message: code {result.rc}")

            time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("Disconnected from MQTT Broker.")

if __name__ == "__main__":
    main()
