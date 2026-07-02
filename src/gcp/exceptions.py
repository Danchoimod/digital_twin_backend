from src.exceptions import GCPIntegrationException


class GCSUploadException(GCPIntegrationException):
    def __init__(self, detail: str = "Failed to upload file to Google Cloud Storage"):
        super().__init__(detail=detail)


class PubSubPublishException(GCPIntegrationException):
    def __init__(self, detail: str = "Failed to publish message to Pub/Sub topic"):
        super().__init__(detail=detail)
