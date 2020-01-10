# (C) Copyright 2018 ZTE corporation.
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

import os
from tempest.lib import decorators

from freezer_tempest_plugin.tests.freezerclient import base


class TestFreezerCmdClient(base.BaseFreezerTest):
    def __init__(self, *args, **kwargs):
        super(TestFreezerCmdClient, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestFreezerCmdClient, self).setUp()
        test_clinet_id = '{"project_id": "tecs",\
            "client_id": "test-tenant_5253_test-hostname_19544",\
            "hostname": "test-hostname_19544",\
            "description": "some usefule text here",\
            "config_id": "config_id_contains_uuid_of_config"\
        }'
        self.environ = super(TestFreezerCmdClient, self).get_environ()
        self.filename = '/tmp/test_client.json'
        os.mknod(self.filename)
        fp = open(self.filename, 'w')
        fp.write(test_clinet_id)

    def tearDown(self):
        super(TestFreezerCmdClient, self).tearDown()
        os.remove(self.filename)

    @decorators.attr(type="gate")
    def test_freezer_cmd_clientlist(self):
        args = ['freezer', 'client-list']

        self.run_subprocess(args, "List of clients registered")

    @decorators.attr(type="gate")
    def test_freezer_cmd_clientregister(self):
        args = ['freezer', 'client-register', '--file',
                '/tmp/test_client.json']

        self.run_subprocess(args, "Register a new client")

    @decorators.attr(type="gate")
    def test_freezer_cmd_clientshow(self):
        args = ['freezer', 'client-show',
                'test-tenant_5253_test-hostname_19544']

        self.run_subprocess(args, "Show a single client")

    @decorators.attr(type="gate")
    def test_freezer_cmd_deleteclient(self):
        args = ['freezer', 'client-delete',
                'test-tenant_5253_test-hostname_19544']

        self.run_subprocess(args, "Delete a client")
