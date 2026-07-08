import os
import logging
from google.cloud import storage, pubsub_v1
from google.oauth2 import service_account

from src.gcp import config

logger = logging.getLogger(__name__)


class GCPClient:
    def __init__(self):
        self.project_id = config.PROJECT_ID
        self.credentials = None

        # Resolve relative path if provided
        cred_path = config.CREDENTIALS_PATH
        if cred_path and not os.path.isabs(cred_path):
            # Resolve relative to the project root directory (one level above 'src')
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(src_dir)
            resolved_path = os.path.normpath(os.path.join(project_root, cred_path))
            if os.path.exists(resolved_path):
                cred_path = resolved_path

        if cred_path and os.path.exists(cred_path):
            try:
                self.credentials = service_account.Credentials.from_service_account_file(
                    cred_path
                )
                logger.info(f"Successfully loaded GCP credentials from: {cred_path}")
            except Exception as e:
                logger.error(f"Error loading credentials file: {e}")

        # Initialize clients lazily
        self._storage_client = None
        self._publisher_client = None

    @property
    def storage_client(self):
        if self._storage_client is None:
            try:
                if self.credentials:
                    self._storage_client = storage.Client(
                        project=self.project_id, credentials=self.credentials
                    )
                else:
                    self._storage_client = storage.Client(project=self.project_id)
            except Exception as e:
                logger.warning(f"Using mock storage client (GCP SDK not fully configured): {e}")
                self._storage_client = None
        return self._storage_client

    @property
    def publisher_client(self):
        if self._publisher_client is None:
            try:
                if self.credentials:
                    self._publisher_client = pubsub_v1.PublisherClient(credentials=self.credentials)
                else:
                    self._publisher_client = pubsub_v1.PublisherClient()
            except Exception as e:
                logger.warning(f"Using mock publisher client (GCP SDK not fully configured): {e}")
                self._publisher_client = None
        return self._publisher_client


gcp_client = GCPClient()
