import os
import json
import logging
import requests
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# Configure premium logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MQTT-PubSub-Bridge")

# Load environment configuration
load_dotenv()

# MQTT configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/data/phupham")
MQTT_KEEP_ALIVE = int(os.getenv("MQTT_KEEP_ALIVE", "60"))

# GCP configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
GCP_PUBSUB_TOPIC = os.getenv("GCP_PUBSUB_TOPIC", "your-pubsub-topic-id")
GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", "")

# Load allowed devices and tokens
# Expected format: JSON map {"device_id": "token"}
try:
    valid_devices_json = os.getenv("VALID_DEVICES", '{"DEVICE_PHU_PHAM_001": "secret_token_123"}')
    VALID_DEVICES = json.loads(valid_devices_json)
except Exception as e:
    logger.error(f"Error parsing VALID_DEVICES environment variable: {e}")
    VALID_DEVICES = {"DEVICE_PHU_PHAM_001": "secret_token_123"}

# Backend URL for token verification
BACKEND_VERIFY_URL = os.getenv("BACKEND_VERIFY_URL", "http://localhost:8000/api/v1/devices/verify")


def verify_device(device_id: str, token: str) -> bool:
    """
    Verifies the device token against the Backend API with a fallback to local environment config.
    """
    if not BACKEND_VERIFY_URL:
        # Fallback if URL is empty
        return VALID_DEVICES.get(device_id) == token

    try:
        response = requests.post(
            BACKEND_VERIFY_URL,
            json={"device_id": device_id, "token": token},
            timeout=5
        )
        if response.status_code == 200:
            logger.info(f"API verification PASSED for device '{device_id}'")
            return True
        elif response.status_code == 401:
            logger.warning(f"API verification FAILED (401 Unauthorized) for device '{device_id}'")
            return False
        else:
            logger.warning(f"Unexpected response code {response.status_code} from verification API. Falling back to local configuration.")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error connecting to verification API: {e}. Falling back to local configuration.")

    # Fallback validation logic
    expected_token = VALID_DEVICES.get(device_id)
    return expected_token == token


# Initialize Google Pub/Sub Publisher client
publisher_client = None
topic_path = None

def init_pubsub():
    global publisher_client, topic_path
    
    if not GCP_PROJECT_ID or GCP_PROJECT_ID == "your-gcp-project-id":
        logger.warning("GCP_PROJECT_ID is not configured. Running bridge in MOCK mode.")
        return

    if not GCP_PUBSUB_TOPIC or GCP_PUBSUB_TOPIC == "your-pubsub-topic-id":
        logger.warning("GCP_PUBSUB_TOPIC is not configured. Running bridge in MOCK mode.")
        return

    try:
        cred_path = GCP_CREDENTIALS_PATH
        if cred_path and not os.path.isabs(cred_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            resolved_path = os.path.join(script_dir, cred_path)
            if os.path.exists(resolved_path):
                cred_path = resolved_path

        if cred_path and os.path.exists(cred_path):
            credentials = service_account.Credentials.from_service_account_file(cred_path)
            publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
            logger.info(f"Initialized GCP Pub/Sub client using service account file: {cred_path}")
        else:
            publisher_client = pubsub_v1.PublisherClient()
            logger.info("Initialized GCP Pub/Sub client using Application Default Credentials (ADC)")
        
        topic_path = publisher_client.topic_path(GCP_PROJECT_ID, GCP_PUBSUB_TOPIC)
        logger.info(f"Target Pub/Sub topic path: {topic_path}")
    except Exception as e:
        logger.error(f"Failed to initialize GCP Pub/Sub Publisher Client: {e}")
        logger.warning("Falling back to MOCK mode for Pub/Sub publishing.")
        publisher_client = None

def publish_to_pubsub(payload: dict):
    if publisher_client is None or topic_path is None:
        logger.info(f"[MOCK-PUBSUB] Successfully published to '{GCP_PUBSUB_TOPIC}': {payload}")
        return

    try:
        data = json.dumps(payload).encode("utf-8")
        # Publish to GCP
        future = publisher_client.publish(topic_path, data)
        message_id = future.result()
        logger.info(f"[GCP-PUBSUB] Published successfully. Message ID: {message_id}")
    except Exception as e:
        logger.error(f"[GCP-PUBSUB] Failed to publish message: {e}")

# MQTT event handlers
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Connected to MQTT Broker. Subscribing to topic: {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"MQTT Connection failed with code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        payload = json.loads(payload_str)
    except Exception as e:
        logger.warning(f"Received malformed or non-JSON message: {e}")
        return

    # 1. Trích xuất device_id và token (chấp nhận cả cấu trúc động mới lẫn cấu trúc cũ)
    raw_payload_data = payload.get("raw_payload", {})
    if isinstance(raw_payload_data, dict):
        device_id = raw_payload_data.get("device_id") or payload.get("device_id")
        token = raw_payload_data.get("token") or payload.get("token")
    else:
        device_id = payload.get("device_id")
        token = payload.get("token")

    if not device_id or not token:
        logger.warning(f"Rejected message from MQTT topic. Missing device_id or token. Payload: {payload}")
        return

    # Verify device credentials using API or local configuration
    if not verify_device(device_id, token):
        logger.warning(f"Authentication FAILED for device '{device_id}'. Rejected forwarding.")
        return

    logger.info(f"Forwarding message from authenticated device '{device_id}' to Pub/Sub...")
    
    # Clean sensitive token from payload before forwarding to Pub/Sub
    pubsub_payload = payload.copy()
    if "token" in pubsub_payload:
        del pubsub_payload["token"]
    if "raw_payload" in pubsub_payload and isinstance(pubsub_payload["raw_payload"], dict):
        # Tạo bản sao sâu cho raw_payload để xoá token, giữ nguyên device_id cho Dataflow/BigQuery nếu cần
        pubsub_payload["raw_payload"] = pubsub_payload["raw_payload"].copy()
        if "token" in pubsub_payload["raw_payload"]:
            del pubsub_payload["raw_payload"]["token"]

    publish_to_pubsub(pubsub_payload)

def main():
    logger.info("Starting MQTT-to-Pub/Sub Bridge...")
    init_pubsub()

    client = mqtt.Client(client_id="mqtt_pubsub_bridge_client")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEP_ALIVE)
    except Exception as e:
        logger.error(f"Could not connect to MQTT Broker: {e}")
        return

    logger.info("Looping network traffic. Press Ctrl+C to stop.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Bridge stopped by user.")
    finally:
        client.disconnect()
        logger.info("MQTT Client disconnected. Bridge shutdown completed.")

if __name__ == "__main__":
    main()
