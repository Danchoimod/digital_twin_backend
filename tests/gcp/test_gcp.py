import io
from src.gcp.utils import upload_to_gcs, publish_pubsub_message


def test_upload_to_gcs_fallback():
    data = io.BytesIO(b"dummy data")
    url = upload_to_gcs(data, "test.txt")
    assert "mock-bucket" in url or "storage.googleapis.com" in url


def test_publish_pubsub_message_fallback():
    msg_id = publish_pubsub_message({"test": "data"})
    assert msg_id is not None
