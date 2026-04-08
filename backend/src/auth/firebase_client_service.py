# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Firebase Auth client initialization."""


import logging
import os

import firebase_admin
import google.auth
from firebase_admin import credentials
from google.auth.exceptions import RefreshError
from google.cloud import resourcemanager_v3

logger = logging.getLogger(__name__)


class FirebaseClient:
    """A class to initialize the Firebase Admin SDK and provide access
    to Firestore and Auth."""

    def __init__(self):
        """Initializes the Firebase Admin SDK with credentials and creates
        a Firestore client."""
        try:
            # Init Firebase Creds
            if not firebase_admin._apps:  # Check if already initialized
                cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

                if cred_path:
                    logger.info(
                        "Initializing Firebase Admin SDK with "
                        "credentials from: %s",
                        cred_path,
                    )
                    if not os.path.exists(cred_path):
                        # If path is provided but file doesn't exist,
                        # it's a configuration error.
                        raise FileNotFoundError(
                            "Firebase credentials file specified but not "
                            f"found at {cred_path}",
                        )
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                else:
                    # If FIREBASE_CREDENTIALS_PATH is not set,
                    # try to initialize with Application Default
                    # Credentials (ADC).
                    # This is typical for Cloud Run, GCE, GKE, App Engine, etc.
                    logger.info("Initializing Firebase Admin SDK using ADC.")
                    firebase_admin.initialize_app()
                    # If ADC are not found or lack permissions, this
                    # will raise an error.
                    # e.g., google.auth.exceptions.DefaultCredentialsError

                logger.info(
                    "Firebase App Name: %s", firebase_admin.get_app().name
                )

                # Check if reauthentication is needed
                self.check_adc_authentication()

        except Exception as e:
            logger.critical(
                "CRITICAL: Error initializing Firebase Admin SDK: %s",
                e,
                exc_info=True,
            )
            msg = f"Failed to initialize Firebase Admin SDK: {e}"
            raise RuntimeError(msg) from e

    def check_adc_authentication(self):
        """Checks if Application Default Credentials (ADC) are valid by making a
        lightweight API call.

        Returns:
            bool: True if authentication is successful, False otherwise.

        """
        try:
            # 1. Attempt to find and load ADC
            creds, project_id = google.auth.default()

            # If no project ID is found, credentials might be for
            # a service account but we need a project to make a test
            # call.
            if not project_id:
                logger.warning(
                    "Could not determine project ID from ADC. "
                    "Unable to perform a live authentication check.",
                )
                # You might still consider this a success if credentials exist
                return creds is not None

            logger.info(
                "ADC found for project: %s. Attempting a test API call...",
                project_id,
            )

            # 2. Make a lightweight, authenticated API call to
            # test the credentials
            client = resourcemanager_v3.ProjectsClient(
                credentials=creds
            )  # type: ignore
            project_name = f"projects/{project_id}"
            client.get_project(
                name=project_name,
            )  # This call requires 'resourcemanager.projects.get' permission

            logger.info("✅ ADC Authentication successful.")
            return True

        except RefreshError as e:
            # This is the specific error for expired user credentials
            logger.critical(
                "❌ ADC REAUTHENTICATION NEEDED. Please run "
                "`gcloud auth application-default login`. Details: %s",
                e,
            )
            raise e
        except Exception as e:
            # Catch other potential exceptions (e.g., permissions,
            # project not found)
            logger.error("An unexpected error occurred during ADC check: %s", e)
            raise e


firebase_client = FirebaseClient()
