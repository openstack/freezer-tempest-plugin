# (C) Copyright 2026 Cleura AB.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from oslo_serialization import jsonutils as json
from tempest.lib import decorators
from tempest.lib import exceptions

from freezer_tempest_plugin.tests.freezer_api.api import base


class TestFreezerApiCentral(base.BaseFreezerApiTest):
    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(TestFreezerApiCentral, cls).setup_clients()
        cls.admin_freezer_api_client = cls.os_admin.freezer_api_client

    @decorators.attr(type="gate")
    def test_only_admin_can_register_central_client(self):
        client_id = 'test-central-client-' + uuid.uuid4().hex[:8]
        client_data = {
            'client_id': client_id,
            'hostname': 'test-host-name',
            'description': 'a test central client',
            'uuid': uuid.uuid4().hex,
            'is_central': True
        }

        # Regular user (primary) should not be allowed to register a
        # central client
        self.assertRaises(exceptions.Forbidden,
                          self.freezer_api_client.post_clients,
                          client_data)

        # Admin user should be allowed to register a central client
        resp, response_body = (
            self.admin_freezer_api_client.post_clients(client_data))
        self.assertEqual(201, resp.status)
        self.addCleanup(
            self.admin_freezer_api_client.delete_clients, client_id)

    @decorators.attr(type="gate")
    def test_trust_creation_and_reuse(self):
        client_id = 'test-central-client-' + uuid.uuid4().hex[:8]
        client_data = {
            'client_id': client_id,
            'hostname': 'test-host-name',
            'description': 'a test central client',
            'uuid': uuid.uuid4().hex,
            'is_central': True
        }

        # Admin registers the central client
        resp, response_body = (
            self.admin_freezer_api_client.post_clients(client_data))
        self.assertEqual(201, resp.status)
        self.addCleanup(
            self.admin_freezer_api_client.delete_clients, client_id)

        # Regular user (primary) creates a job targeting the central client
        job_data = {
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "backup",
                        "mode": "fs",
                        "path_to_backup": "/tmp/dummy",
                        "backup_name": "dummy_backup",
                        "container": "dummy_container",
                    },
                    "exit_status": "success",
                    "max_retries": 1,
                    "max_retries_interval": 1,
                    "mandatory": True
                }
            ],
            "job_schedule": {
                "status": "stop",
            },
            "client_id": client_id,
            "description": "test central job 1"
        }

        resp, response_body = self.freezer_api_client.post_jobs(job_data)
        self.assertEqual(201, resp.status)
        job_id_1 = response_body['job_id']
        self.addCleanup(self.freezer_api_client.delete_jobs, job_id_1)

        # Verify that a trust was created and added to the job
        resp, response_body = self.freezer_api_client.get_jobs(job_id_1)
        self.assertEqual(200, resp.status)
        job_1_details = json.loads(response_body)
        self.assertIn('user_credentials', job_1_details)
        trust_id_1 = job_1_details['user_credentials'].get('trust_id')
        self.assertIsNotNone(trust_id_1)

        # Create a second job targeting the same central client
        job_data_2 = job_data.copy()
        job_data_2['description'] = "test central job 2"

        resp, response_body = self.freezer_api_client.post_jobs(job_data_2)
        self.assertEqual(201, resp.status)
        job_id_2 = response_body['job_id']
        self.addCleanup(self.freezer_api_client.delete_jobs, job_id_2)

        # Verify that the trust was reused (the trust_id is identical)
        resp, response_body = self.freezer_api_client.get_jobs(job_id_2)
        self.assertEqual(200, resp.status)
        job_2_details = json.loads(response_body)
        self.assertIn('user_credentials', job_2_details)
        trust_id_2 = job_2_details['user_credentials'].get('trust_id')
        self.assertEqual(trust_id_1, trust_id_2)
