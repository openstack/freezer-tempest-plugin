# (C) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

from freezer_tempest_plugin.tests.freezer.agent import base


class TestFreezerTestsRunning(base.BaseFreezerTest):

    @decorators.attr(type="gate")
    def test_tests_running(self):
        # See if tempest plugin tests run.
        self.assertEqual(1, 1, 'Tests are running')
