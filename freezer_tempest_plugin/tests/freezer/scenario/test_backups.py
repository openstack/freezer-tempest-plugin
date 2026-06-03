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

import hashlib
import os
import shutil
import subprocess
import tempfile
import time

from tempest import config
from tempest.lib.cli import base as cli_base
from tempest.lib.cli import output_parser
from tempest.lib import decorators
from tempest.lib import exceptions

from oslo_serialization import jsonutils as json

from freezer_tempest_plugin.tests.freezer.agent import base
CONF = config.CONF

JOB_TABLE_RESULT_COLUMN = 3


class BaseFreezerCliTest(base.BaseFreezerTest):
    """Base test case class for all Freezer API tests."""

    credentials = ['primary']

    @classmethod
    def setup_clients(cls):
        super(BaseFreezerCliTest, cls).setup_clients()

        cls.cli = CLIClientWithFreezer(
            username=cls.os_primary.credentials.username,
            # fails if the password contains an unescaped $ sign
            password=cls.os_primary.credentials.password.replace('$', '$$'),
            tenant_name=cls.os_primary.credentials.project_name,
            uri=cls.get_auth_url(),
            cli_dir='/usr/local/bin'  # devstack default
        )
        cls.cli.cli_dir = ''

        if hasattr(cls, 'os_admin'):
            cls.admin_cli = CLIClientWithFreezer(
                username=cls.os_admin.credentials.username,
                # fails if the password contains an unescaped $ sign
                password=cls.os_admin.credentials.password.replace('$', '$$'),
                tenant_name=cls.os_admin.credentials.project_name,
                uri=cls.get_auth_url(),
                cli_dir='/usr/local/bin'  # devstack default
            )
            cls.admin_cli.cli_dir = ''

    def setUp(self):
        super(BaseFreezerCliTest, self).setUp()
        self.schedulers = []

    def tearDown(self):
        for proc in self.schedulers:
            try:
                proc.terminate()
                proc.wait()
            except Exception:
                pass
        super(BaseFreezerCliTest, self).tearDown()

    def _get_service_credentials(self):
        """Try to load freezer service credentials from freezer-api.conf"""
        config_path = '/etc/freezer/freezer-api.conf'
        if os.path.exists(config_path):
            import configparser
            config = configparser.ConfigParser()
            try:
                config.read(config_path)
                if config.has_section('keystone_authtoken'):
                    sect = 'keystone_authtoken'
                    return {
                        'username': config.get(sect, 'username',
                                               fallback=None),
                        'password': config.get(sect, 'password',
                                               fallback=None),
                        'project_name': config.get(sect, 'project_name',
                                                   fallback=None),
                        'user_domain_name': config.get(
                            sect, 'user_domain_name', fallback='Default'),
                        'project_domain_name': config.get(
                            sect, 'project_domain_name', fallback='Default'),
                    }
            except Exception:
                pass
        return None

    def _start_scheduler(self, client_id, jobs_dir,
                         centralized=False, extra_flags=None):
        cmd = [
            'freezer-scheduler',
            '--debug',
            '--scheduler-no-daemon',
            '-c', client_id,
            '-f', jobs_dir,
            '--os-endpoint-type', 'publicURL'
        ]
        if centralized:
            cmd.append('--scheduler-centralized-scheduler')
        if extra_flags:
            cmd.extend(extra_flags)

        ca_cert = (os.environ.get('OS_CACERT')
                   or CONF.identity.ca_certificates_file)
        if ca_cert:
            cmd += ['--os-cacert', ca_cert]
        project_domain = (
            getattr(CONF.identity,
                    'project_domain_name', None)
            or 'Default')
        user_domain = (
            getattr(CONF.identity,
                    'user_domain_name', None)
            or 'Default')
        cmd += ['--os-project-domain-name', project_domain]
        cmd += ['--os-user-domain-name', user_domain]
        cmd += ['start']

        env = os.environ.copy()
        if centralized:
            service_creds = self._get_service_credentials()
            if service_creds:
                env['OS_USERNAME'] = service_creds['username']
                env['OS_PASSWORD'] = service_creds['password']
                env['OS_PROJECT_NAME'] = service_creds['project_name']
                env['OS_TENANT_NAME'] = service_creds['project_name']
                env['OS_PROJECT_DOMAIN_NAME'] = (
                    service_creds['project_domain_name'])
                env['OS_USER_DOMAIN_NAME'] = (
                    service_creds['user_domain_name'])
            else:
                env['OS_USERNAME'] = (
                    self.os_admin.credentials.username)
                env['OS_PASSWORD'] = (
                    self.os_admin.credentials.password)
                env['OS_PROJECT_NAME'] = (
                    self.os_admin.credentials.project_name)
                env['OS_TENANT_NAME'] = (
                    self.os_admin.credentials.project_name)
                env['OS_PROJECT_DOMAIN_NAME'] = (
                    self.os_admin.credentials.project_domain_name)
                env['OS_USER_DOMAIN_NAME'] = (
                    self.os_admin.credentials.user_domain_name)
        env['OS_AUTH_URL'] = self.get_auth_url()

        # Write stdout/stderr to LOGDIR or fallback to jobs_dir
        log_dir = os.environ.get('LOGDIR') or '/opt/stack/logs'
        if not os.path.exists(log_dir) or not os.access(log_dir, os.W_OK):
            log_dir = jobs_dir
        log_path = os.path.join(
            log_dir, 'freezer-scheduler-{}.log'.format(client_id))

        with open(log_path, 'w') as log_file:
            proc = subprocess.Popen(
                cmd, env=env,
                stdout=log_file, stderr=log_file)
        self.schedulers.append(proc)
        return proc

    def wait_for_client_registration(self, client_id, timeout=160):
        start = time.time()
        while True:
            try:
                output = self.cli.freezer_client(action='client-list',
                                                 merge_stderr=False)
                if client_id in output:
                    return client_id
            except Exception:
                pass

            if time.time() - start > timeout:
                self.fail("Client '{}' not registered after {}s"
                          .format(client_id, timeout))
            time.sleep(10)

    def delete_job(self, job_id):
        self.cli.freezer_client(action='job-delete', params=job_id)

    def create_job(self, job_json):

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as job_file:
            job_file.write(json.dumps(job_json))
            job_file.flush()

            output = self.cli.freezer_client(
                action='job-create',
                params='-f json --file {} --client {}'.format(
                    job_file.name,
                    job_json['client_id']),
                merge_stderr=False)
            job_result = json.loads(output)
            expected = {
                "Job ID": job_result['Job ID'],
                "Client ID": job_json['client_id'],
                "User ID": self.os_primary.credentials.user_id,
                "Session ID": "",
                "Description": job_json['description'],
                "Start Date": "",
                "End Date": "",
                "Interval": "",
                "Status": "",
                "Result": "",
                "Current pid": "",
                "Event": ""
            }
            # NOTE: it's kinda hard to compare strings that should be json
            del job_result['Actions']
            self.assertEqual(expected, job_result)

            self.addCleanup(self.delete_job, job_result['Job ID'])

            return job_result['Job ID']

    def find_job_in_job_list(self, job_id, client_id='test_node'):
        job_list = output_parser.table(
            self.cli.freezer_client(
                action='job-list', params='-C {}'.format(client_id)))

        for row in job_list['values']:
            if row[0].strip() == job_id.strip():
                return row

        self.fail('Could not find job: {}'.format(job_id))

    def wait_for_job_status(self, job_id, client_id='test_node', timeout=720):
        start = time.time()

        while True:
            row = self.find_job_in_job_list(job_id, client_id=client_id)

            if row[JOB_TABLE_RESULT_COLUMN]:
                return
            elif time.time() - start > timeout:
                self.fail("Status of job '{}' is '{}'."
                          .format(job_id, row[JOB_TABLE_RESULT_COLUMN]))
            else:
                time.sleep(5)

    def assertJobColumnEqual(self, job_id, column, expected,
                             client_id='test_node'):
        row = self.find_job_in_job_list(job_id, client_id=client_id)
        self.assertEqual(expected, row[column])


class CLIClientWithFreezer(cli_base.CLIClient):
    def freezer_scheduler(self, action, flags='', params='', fail_ok=False,
                          endpoint_type='publicURL', merge_stderr=False):
        """Executes freezer-scheduler command for the given action.

        :param action: the cli command to run using freezer-scheduler
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """

        flags += ' --os-endpoint-type %s' % endpoint_type
        ca_cert = \
            os.environ.get('OS_CACERT') or CONF.identity.ca_certificates_file
        if ca_cert:
            flags += ' --os-cacert %s' % ca_cert
        project_domain = getattr(
            CONF.identity, 'project_domain_name', None) or 'Default'
        user_domain = getattr(
            CONF.identity, 'user_domain_name', None) or 'Default'
        flags += ' --os-project-domain-name %s' % project_domain
        flags += ' --os-user-domain-name %s' % user_domain

        return self.cmd_with_auth(
            'freezer-scheduler', action, flags, params, fail_ok, merge_stderr)

    def freezer_client(self, action, flags='', params='', fail_ok=False,
                       endpoint_type='publicURL', merge_stderr=True):
        flags += ' --os-endpoint-type %s' % endpoint_type
        ca_cert = \
            os.environ.get('OS_CACERT') or CONF.identity.ca_certificates_file
        if ca_cert:
            flags += ' --os-cacert %s' % ca_cert
        project_domain = getattr(
            CONF.identity, 'project_domain_name', None) or 'Default'
        user_domain = getattr(
            CONF.identity, 'user_domain_name', None) or 'Default'
        flags += ' --os-project-domain-name %s' % project_domain
        flags += ' --os-user-domain-name %s' % user_domain
        return self.cmd_with_auth(
            'freezer', action, flags, params, fail_ok, merge_stderr)


# This class is just copied from the freezer repo. Depending on where the
# scenario tests end up we may need to refactore this.
class Temp_Tree(object):
    def __init__(self, suffix='', dir=None, create=True):
        self.create = create
        if create:
            self.path = tempfile.mkdtemp(dir=dir, prefix='__freezer_',
                                         suffix=suffix)
        else:
            self.path = dir
        self.files = []

    def __enter__(self):
        return self

    def cleanup(self):
        if self.create and self.path:
            shutil.rmtree(self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def add_random_data(self, ndir=5, nfile=5, size=1024):
        """
        add some files containing randoma data

        :param ndir: number of dirs to create
        :param nfile: number of files to create in each dir
        :param size: size of files
        :return: None
        """
        for x in range(ndir):
            subdir_path = tempfile.mkdtemp(dir=self.path)
            for y in range(nfile):
                abs_pathname = self.create_file_with_random_data(
                    dir_path=subdir_path, size=size)
                rel_path_name = abs_pathname[len(self.path) + 1:]
                self.files.append(rel_path_name)

    def create_file_with_random_data(self, dir_path, size=1024):
        handle, abs_pathname = tempfile.mkstemp(dir=dir_path)
        with open(abs_pathname, 'wb') as fd:
            fd.write(os.urandom(size))
        return abs_pathname

    def get_file_hash(self, rel_filepath):
        filepath = os.path.join(self.path, rel_filepath)
        if os.path.isfile(filepath):
            return self._filehash(filepath)
        else:
            return ''

    def _filehash(self, filepath):
        """
        Get GIT style sha1 hash for a file

        :param filepath: path of file to hash
        :return: hash of the file
        """
        filesize_bytes = os.path.getsize(filepath)
        hash_obj = hashlib.sha1()
        hash_obj.update(("blob %u\0" % filesize_bytes).encode('utf-8'))
        with open(filepath, 'rb') as handle:
            hash_obj.update(handle.read())
        return hash_obj.hexdigest()

    def get_file_list(self):
        """
        walks the dir tree and creates a list of relative pathnames
        :return: list of relative file paths
        """
        self.files = []
        for root, dirs, files in os.walk(self.path):
            rel_base = root[len(self.path) + 1:]
            self.files.extend([os.path.join(rel_base, x) for x in files])
        return self.files

    def is_equal(self, other_tree):
        """
        Checks whether two dir tree contain the same files
        It checks the number of files and the hash of each file.

        NOTE: tox puts .coverage files in the temp folder (?)

        :param other_tree: dir tree to compare with
        :return: true if the dir trees contain the same files
        """
        lh_files = [x for x in sorted(self.get_file_list())
                    if not x.startswith('.coverage')]
        rh_files = [x for x in sorted(other_tree.get_file_list())
                    if not x.startswith('.coverage')]
        if lh_files != rh_files:
            return False
        for fname in lh_files:
            if os.path.isfile(fname):
                if self.get_file_hash(fname) != \
                        other_tree.get_file_hash(fname):
                    return False
        return True


class TestFreezerScenario(BaseFreezerCliTest):
    def setUp(self):
        super(TestFreezerScenario, self).setUp()
        self.source_tree = Temp_Tree()
        self.source_tree.add_random_data()
        self.dest_tree = Temp_Tree()

        self.jobs_dir = tempfile.mkdtemp(
            prefix='freezer_tempest_job_dir_')
        self.addCleanup(shutil.rmtree, self.jobs_dir)

        self._start_scheduler('test_node', self.jobs_dir)
        self.client_id = self.wait_for_client_registration(
            'test_node')

    def tearDown(self):
        super(TestFreezerScenario, self).tearDown()
        self.source_tree.cleanup()
        self.dest_tree.cleanup()
        self.cli.freezer_client(
            action='client-delete', params=self.client_id)

    def test_simple_backup(self):
        backup_job = {
            "client_id": "test_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "backup",
                        "mode": "fs",
                        "storage": "local",
                        "backup_name": "backup1",
                        "path_to_backup": self.source_tree.path,
                        "container": "/tmp/freezer_test/",
                    },
                    "max_retries": 3,
                    "max_retries_interval": 60
                }
            ],
            "description": "a test backup"
        }
        restore_job = {
            "client_id": "test_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "restore",
                        "storage": "local",
                        "restore_abs_path": self.dest_tree.path,
                        "backup_name": "backup1",
                        "container": "/tmp/freezer_test/",
                    },
                    "max_retries": 3,
                    "max_retries_interval": 60
                }
            ],
            "description": "a test restore"
        }

        backup_job_id = self.create_job(backup_job)
        self.cli.freezer_client(action='job-start', params=backup_job_id)
        self.wait_for_job_status(backup_job_id)
        self.assertJobColumnEqual(backup_job_id, JOB_TABLE_RESULT_COLUMN,
                                  'success')

        restore_job_id = self.create_job(restore_job)
        self.wait_for_job_status(restore_job_id)
        self.assertJobColumnEqual(restore_job_id, JOB_TABLE_RESULT_COLUMN,
                                  'success')

        self.assertTrue(self.source_tree.is_equal(self.dest_tree))


class TestFreezerCentralScenario(BaseFreezerCliTest):
    credentials = ['primary', 'admin']

    def setUp(self):
        super(TestFreezerCentralScenario, self).setUp()
        self.source_tree = Temp_Tree()
        self.source_tree.add_random_data()
        self.dest_tree = Temp_Tree()

        self.central_jobs_dir = tempfile.mkdtemp(
            prefix='freezer_central_job_dir_')
        self.addCleanup(shutil.rmtree, self.central_jobs_dir)
        self.restricted_jobs_dir = tempfile.mkdtemp(
            prefix='freezer_restricted_job_dir_')
        self.addCleanup(shutil.rmtree, self.restricted_jobs_dir)

        # Start central scheduler as admin
        self._start_scheduler(
            'central_node', self.central_jobs_dir,
            centralized=True)
        self.client_id = self.wait_for_client_registration(
            'central_node')

    def tearDown(self):
        super(TestFreezerCentralScenario, self).tearDown()
        self.source_tree.cleanup()
        self.dest_tree.cleanup()

        service_creds = self._get_service_credentials()
        if service_creds:
            try:
                service_cli = CLIClientWithFreezer(
                    username=service_creds['username'],
                    password=service_creds['password'].replace('$', '$$'),
                    tenant_name=service_creds['project_name'],
                    uri=self.get_auth_url(),
                    cli_dir=''
                )
                service_cli.freezer_client(
                    action='client-delete',
                    params=self.client_id,
                    fail_ok=True)
            except Exception:
                pass
        else:
            self.admin_cli.freezer_client(
                action='client-delete',
                params=self.client_id,
                fail_ok=True)

    @decorators.attr(type="gate")
    def test_freezer_client_shows_central_clients_to_other_users(self):
        output = self.cli.freezer_client(action='client-list')
        self.assertIn('central_node', output)

    @decorators.attr(type="gate")
    def test_central_scheduler_ignores_job_without_trust(self):
        # Create a backup job targeting the central client
        backup_job = {
            "client_id": "central_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "backup",
                        "mode": "fs",
                        "storage": "local",
                        "backup_name": "no_trust_backup",
                        "path_to_backup": self.source_tree.path,
                        "container": "/tmp/freezer_no_trust/",
                    },
                    "max_retries": 1,
                    "max_retries_interval": 10
                }
            ],
            "description": "no trust test backup"
        }
        job_id = self.create_job(backup_job)

        # Regular user (primary) updates the job to remove user_credentials
        # (removing the trust)
        update_json = {
            "user_credentials": {}
        }
        with tempfile.NamedTemporaryFile(
                mode='w', delete=False) as update_file:
            update_file.write(json.dumps(update_json))
            update_file.flush()
            self.addCleanup(os.remove, update_file.name)
            self.cli.freezer_client(
                action='job-update',
                params='{} {}'.format(job_id, update_file.name)
            )

        # Try to start the job
        self.cli.freezer_client(action='job-start', params=job_id)

        # Wait a few seconds to let scheduler poll/process it
        time.sleep(10)

        # Assert status remains empty/unchanged (it wasn't executed)
        self.assertJobColumnEqual(
            job_id, JOB_TABLE_RESULT_COLUMN, '', client_id='central_node')

    @decorators.attr(type="gate")
    def test_scheduler_capabilities_restriction(self):
        # Start a restricted scheduler on primary node
        self._start_scheduler(
            'cap_node',
            self.restricted_jobs_dir,
            centralized=False,
            extra_flags=[
                '--capabilities-supported-actions', 'restore',
                '--capabilities-supported-storages', 'swift',
                '--capabilities-supported-engines', 'nova'
            ]
        )
        self.wait_for_client_registration('cap_node')

        self.addCleanup(
            self.cli.freezer_client,
            action='client-delete', params='cap_node')

        # 1. Job requiring forbidden action "backup"
        job_actions_forbidden = {
            "client_id": "cap_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "backup",
                        "mode": "fs",
                        "storage": "swift",
                        "engine": "nova",
                        "engine_name": "nova",
                        "backup_name": "cap_backup1",
                        "container": "container1"
                    }
                }
            ],
            "description": "restricted action job"
        }
        self.assertRaises(exceptions.CommandFailed,
                          self.create_job, job_actions_forbidden)

        # 2. Job requiring forbidden storage "local" (locking local storage)
        job_storage_forbidden = {
            "client_id": "cap_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "restore",
                        "mode": "fs",
                        "storage": "local",
                        "engine": "nova",
                        "engine_name": "nova",
                        "backup_name": "cap_backup2",
                        "container": "container2"
                    }
                }
            ],
            "description": "restricted storage job"
        }
        self.assertRaises(exceptions.CommandFailed,
                          self.create_job, job_storage_forbidden)

        # 3. Job requiring forbidden engine "tar"
        job_engine_forbidden = {
            "client_id": "cap_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "restore",
                        "mode": "fs",
                        "storage": "swift",
                        "engine": "tar",
                        "engine_name": "tar",
                        "backup_name": "cap_backup3",
                        "container": "container3"
                    }
                }
            ],
            "description": "restricted engine job"
        }
        self.assertRaises(exceptions.CommandFailed,
                          self.create_job, job_engine_forbidden)

        # 4. Allowed job matching restricted capabilities
        job_allowed = {
            "client_id": "cap_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "restore",
                        "mode": "fs",
                        "storage": "swift",
                        "engine": "nova",
                        "engine_name": "nova",
                        "backup_name": "cap_backup_allowed",
                        "container": "container_allowed"
                    }
                }
            ],
            "description": "allowed job"
        }
        job_id_allowed = self.create_job(job_allowed)
        self.cli.freezer_client(action='job-start', params=job_id_allowed)

        # Wait a few seconds to let scheduler poll/process it
        # Since it's allowed, scheduler should process it and status
        # will become non-empty (e.g., 'fail' or similar).
        self.wait_for_job_status(job_id_allowed, client_id='cap_node')

    @decorators.attr(type="gate")
    def test_central_backup_restore_flow(self):
        backup_job = {
            "client_id": "central_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "backup",
                        "mode": "fs",
                        "storage": "local",
                        "backup_name": "central_backup",
                        "path_to_backup": self.source_tree.path,
                        "container": "/tmp/freezer_central_test/",
                    },
                    "max_retries": 3,
                    "max_retries_interval": 60
                }
            ],
            "description": "a central test backup"
        }
        restore_job = {
            "client_id": "central_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "restore",
                        "storage": "local",
                        "restore_abs_path": self.dest_tree.path,
                        "backup_name": "central_backup",
                        "container": "/tmp/freezer_central_test/",
                    },
                    "max_retries": 3,
                    "max_retries_interval": 60
                }
            ],
            "description": "a central test restore"
        }

        backup_job_id = self.create_job(backup_job)
        self.cli.freezer_client(action='job-start', params=backup_job_id)
        self.wait_for_job_status(backup_job_id, client_id='central_node')
        self.assertJobColumnEqual(
            backup_job_id, JOB_TABLE_RESULT_COLUMN, 'success',
            client_id='central_node')

        restore_job_id = self.create_job(restore_job)
        self.wait_for_job_status(restore_job_id, client_id='central_node')
        self.assertJobColumnEqual(
            restore_job_id, JOB_TABLE_RESULT_COLUMN, 'success',
            client_id='central_node')

        self.assertTrue(self.source_tree.is_equal(self.dest_tree))
