# (C) Copyright 2018 ZTE corporation
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
from tempest.lib import decorators

from freezer_tempest_plugin.tests.freezerclient import base


class TestFreezerCmdBackup(base.BaseFreezerTest):
    def __init__(self, *args, **kwargs):
        super(TestFreezerCmdBackup, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestFreezerCmdBackup, self).setUp()
        self.environ = super(TestFreezerCmdBackup, self).get_environ()

    def tearDown(self):
        super(TestFreezerCmdBackup, self).tearDown()

    @decorators.attr(type="gate")
    def test_freezer_cmd_backuplist(self):
        args = ['freezer', 'backup-list']

        self.run_subprocess(args, " List all backups")
