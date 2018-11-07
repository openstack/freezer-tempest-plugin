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
from freezer_tempest_plugin.tests.scheduler import base
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
    def test_freezer_schedulers_restart(self):
        args = ['freezer-scheduler', 'restart']

        self.run_subprocess(args, "Freezer scheduler restart.")

    @decorators.attr(type="gate")
    def test_freezer_schedulers_stop(self):
        args = ['freezer-scheduler', 'stop']

        self.run_subprocess(args, "Freezer scheduler stop")

    @decorators.attr(type="gate")
    def test_freezer_schedulers_start(self):
        args = ['freezer-scheduler', 'start']

        self.run_subprocess(args, "Freezer scherduler start")

    @decorators.attr(type="gate")
    def test_freezer_schedulers_reload(self):
        args = ['freezer-scheduler', 'reload']

        self.run_subprocess(args, "Freezer scheduler reload")

    @decorators.attr(type="gate")
    def test_freezer_schedulers_status(self):
        args = ['freezer-scheduler', 'status']

        self.run_subprocess(args, "Freezer scheduler status")
