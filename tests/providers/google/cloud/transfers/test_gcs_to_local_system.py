#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import os

import pytest

from airflow.providers.google.cloud.example_dags.example_gcs_to_local import (
    BUCKET,
    PATH_TO_LOCAL_FILE,
    PATH_TO_REMOTE_FILE,
)
from tests.providers.google.cloud.utils.gcp_authenticator import GCP_GCS_KEY
from tests.test_utils.gcp_system_helpers import CLOUD_DAG_FOLDER, GoogleSystemTest, provide_gcp_context


@pytest.mark.backend("mysql", "postgres")
@pytest.mark.credential_file(GCP_GCS_KEY)
class GoogleCloudStorageToLocalExampleDagsTest(GoogleSystemTest):
    @provide_gcp_context(GCP_GCS_KEY)
    def setUp(self):
        super().setUp()
        self.create_gcs_bucket(BUCKET)
        self.upload_content_to_gcs(
            lines=f"{os.urandom(1 * 1024 * 1024)}", bucket=BUCKET, filename=PATH_TO_REMOTE_FILE
        )

    @provide_gcp_context(GCP_GCS_KEY)
    def tearDown(self):
        self.delete_gcs_bucket(BUCKET)
        os.remove(PATH_TO_LOCAL_FILE)
        super().tearDown()

    @provide_gcp_context(GCP_GCS_KEY)
    def test_run_example_dag(self):
        self.run_dag('example_gcs_to_local', CLOUD_DAG_FOLDER)
