# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for the Python logging handlers."""

import base64
import sys
import json
import threading
import traceback

from google.cloud import pubsub_v1

from pubsub_logging.errors import RecoverableError

PUBSUB_SCOPES = ["https://www.googleapis.com/auth/pubsub"]

clients = threading.local()

published_client = pubsub_v1.PublisherClient()


def compat_urlsafe_b64encode(v):
    """A urlsafe ba64encode which is compatible with Python 2 and 3.

    Args:
      v: A string to encode.
    Returns:
      The encoded string.
    """
    if sys.version_info[0] >= 3:  # pragma: NO COVER
        return base64.urlsafe_b64encode(v.encode('UTF-8')).decode('ascii')
    else:
        return base64.urlsafe_b64encode(v)


def get_pubsub_client(http=None, credentials=None):
    """Return a Pub/Sub client.

    Args:
      http: httplib2.Http instance. Defaults to None.
    Returns:
      Cloud Pub/Sub client.
    """

    return published_client


def check_topic(client, project_id, topic):
    """Checks the existance of a topic of the given name.

    Args:
      client: Cloud Pub/Sub client.
      project_id: project id
      topic: topic name that we publish the records to.
      retry: number of retry upon intermittent failures, defaults to 3.

    Returns:
      True when it confirmed that the topic exists, and False otherwise.
    """

    try:
        client.topic_path(project_id, topic)
        return True
    except Exception:
        traceback.print_exc(file=sys.stderr)
    return False


def publish_body(client, body, project_id, topic):
    """Publishes the specified body to Cloud Pub/Sub.

    Args:
      client: Cloud Pub/Sub client.
      body: Post body for Pub/Sub publish call.
      project_id: project id
      topic: topic name that we publish the records to.
      retry: number of retry upon intermittent failures.

    Raises:
      errors.HttpError When the Cloud Pub/Sub API call fails with
                       unrecoverable reasons.
      RecoverableError When the Cloud Pub/Sub API call fails with
                       intermittent errors.
    """
    try:
        topic_path = client.topic_path(project_id, topic)
        client.publish(topic_path, data=json.dumps(body).encode())
    except Exception as e:
        err_str = str(e)

        if '200' not in err_str:
            # Publishing failed for some non-recoverable reason. For
            # example, perhaps the service account doesn't have a
            # permission to publish to the specified topic, or the topic
            # simply doesn't exist.
            raise
        else:
            # Treat this as a recoverable error.
            raise RecoverableError()
