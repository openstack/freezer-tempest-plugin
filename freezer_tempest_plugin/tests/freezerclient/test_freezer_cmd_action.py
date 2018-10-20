# (C) opyright 2018 ZTE Corporation.
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
from freezer_tempest_plugin.tests.freezerclient import base
from tempest.lib import decorators


class TestFreezerCmdAction(base.BaseFreezerTest):
    def __init__(self, *args, **kwargs):
        super(TestFreezerCmdAction, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestFreezerCmdAction, self).setUp()
        self.environ = super(TestFreezerCmdAction, self).get_environ()

    def tearDown(self):
        super(TestFreezerCmdAction, self).tearDown()

    @decorators.attr(type="gate")
    def test_freezer_cmd_actionlist(self):
        args = ['freezer', 'action-list']

        self.run_subprocess(args, "List all actions")
