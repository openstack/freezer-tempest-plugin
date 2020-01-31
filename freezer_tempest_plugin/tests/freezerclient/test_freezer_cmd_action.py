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
import os
from tempest.lib import decorators

from freezer_tempest_plugin.tests.freezerclient import base


class TestFreezerCmdAction(base.BaseFreezerTest):
    def __init__(self, *args, **kwargs):
        super(TestFreezerCmdAction, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestFreezerCmdAction, self).setUp()
        test_action_id = '{\
            "freezer_action":\
             {\
               "action": "backup",\
               "mode": "fs",\
               "path_to_backup": "/tmp/source",\
               "backup_name": "my-first-backup",\
               "container": "/tmp/backup/",\
               "storage": "local"\
              },\
             "max_retries": 3,\
             "max_retries_interval": 60\
        }'
        self.environ = super(TestFreezerCmdAction, self).get_environ()
        self.filename = '/tmp/test_action.json'
        if os.path.exists(self.filename):
            os.remove(self.filename)
        os.mknod(self.filename)
        fp = open(self.filename, 'w')
        fp.write(test_action_id)

    def tearDown(self):
        super(TestFreezerCmdAction, self).tearDown()

    @decorators.attr(type="gate")
    def test_freezer_cmd_actioncreate(self):
        args = ['freezer', 'action-create', '--file',
                self.filename]

        self.run_subprocess(args, "Create a new action")

    @decorators.attr(type="gate")
    def test_freezer_cmd_actionlist(self):
        args = ['freezer', 'action-list']

        self.run_subprocess(args, "List all actions")

    @decorators.attr(type="gate")
    def test_freezer_cmd_actionshow(self):
        args = ['freezer', 'action-create', '--file',
                self.filename]
        out, err = self.run_subprocess(args, "Create a new action")
        action_id = err.split(' ')[1]

        args = ['freezer', 'action-show', action_id]

        self.run_subprocess(args, "show a action")

    @decorators.attr(type="gate")
    def test_freezer_cmd_actiondelete(self):
        args = ['freezer', 'action-create', '--file',
                self.filename]
        out, err = self.run_subprocess(args, "Create a new action")
        action_id = err.split(' ')[1]

        args = ['freezer', 'action-delete', action_id]

        self.run_subprocess(args, "delete a action")
