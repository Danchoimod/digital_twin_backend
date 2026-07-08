import os
import time
import logging
from dotenv import load_dotenv
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# Configure premium logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("GCP-Subscriber")

# Load environment configuration
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "automatic-vent-443012-g2")
GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", "automatic-vent-443012-g2-288bd683bf67.json")
# Use the subscription name provided
SUBSCRIPTION_NAME = "digital_twin-sub"

def callback(message):
    logger.info(f"Received message from GCP Pub/Sub: {message.data.decode('utf-8')}")
    # Acknowledge the message so it's removed from the queue
    message.ack()

def main():
    logger.info("Initializing GCP Pub/Sub Subscriber...")
    
    # Resolve credential path relative to this script's directory if not absolute
    cred_path = GCP_CREDENTIALS_PATH
    if cred_path and not os.path.isabs(cred_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        resolved_path = os.path.join(script_dir, cred_path)
        if os.path.exists(resolved_path):
            cred_path = resolved_path

    try:
        if cred_path and os.path.exists(cred_path):
            credentials = service_account.Credentials.from_service_account_file(cred_path)
            subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
            logger.info(f"Initialized GCP Subscriber client using file: {cred_path}")
        else:
            subscriber = pubsub_v1.SubscriberClient()
            logger.info("Initialized GCP Subscriber client using Application Default Credentials (ADC)")
        
        subscription_path = subscriber.subscription_path(GCP_PROJECT_ID, SUBSCRIPTION_NAME)
        logger.info(f"Listening for messages on: {subscription_path}")
        
        # Subscribe to subscription queue
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
        
        logger.info("Subscriber loop started. Press Ctrl+C to exit.")
        # Wrap in a try-except to keep thread open
        with subscriber:
            streaming_pull_future.result()
            
    except KeyboardInterrupt:
        logger.info("Subscriber stopped by user.")
    except Exception as e:
        logger.error(f"Error running subscriber: {e}")

if __name__ == "__main__":
    main()
