import json
import logging
from typing import BinaryIO

from src.gcp.client import gcp_client
from src.gcp import config
from src.gcp.exceptions import GCSUploadException, PubSubPublishException

logger = logging.getLogger(__name__)


def upload_to_gcs(file_obj: BinaryIO, destination_blob_name: str) -> str:
    """
    Uploads a file to Google Cloud Storage.
    Returns the public URL of the uploaded object.
    """
    bucket_name = config.STORAGE_BUCKET
    if not bucket_name:
        logger.warning("STORAGE_BUCKET not configured. Mocking GCS upload.")
        return f"https://storage.googleapis.com/mock-bucket/{destination_blob_name}"

    try:
        client = gcp_client.storage_client
        if client is None:
            raise GCSUploadException("GCS storage client is uninitialized")
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        
        # Upload
        file_obj.seek(0)
        blob.upload_from_file(file_obj)
        return blob.public_url
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        raise GCSUploadException(str(e))


def publish_pubsub_message(payload: dict, attributes: dict = None) -> str:
    """
    Publishes a message to a GCP Pub/Sub Topic.
    Returns the published message ID.
    """
    topic_id = config.PUBSUB_TOPIC
    project_id = config.PROJECT_ID

    if not topic_id or not project_id:
        logger.warning("GCP Project ID or Topic ID not configured. Mocking Pub/Sub publish.")
        return "mock_message_id_12345"

    try:
        publisher = gcp_client.publisher_client
        if publisher is None:
            raise PubSubPublishException("Pub/Sub publisher client is uninitialized")

        topic_path = publisher.topic_path(project_id, topic_id)
        data = json.dumps(payload).encode("utf-8")
        
        attrs = attributes or {}
        future = publisher.publish(topic_path, data, **attrs)
        return future.result()
    except Exception as e:
        logger.error(f"Pub/Sub publish failed: {e}")
        raise PubSubPublishException(str(e))
