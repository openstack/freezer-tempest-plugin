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

# import urllib

import urllib.parse

from oslo_log import log
from oslo_serialization import jsonutils as json
from tempest import config
from tempest.lib.common import rest_client

CONF = config.CONF
LOG = log.getLogger(__name__)


class FreezerApiClient(rest_client.RestClient):
    def __init__(self, auth_provider):
        super(FreezerApiClient, self).__init__(
            auth_provider,
            CONF.backup.catalog_type,
            CONF.backup.region or CONF.identity.region,
            endpoint_type=CONF.backup.endpoint_type
        )
        LOG.info(self)
        if self.tenant_id:
            LOG.info(self.tenant_id)

    def get_version(self):
        resp, response_body = self.get('/')
        return resp, response_body

    def get_version_v1(self):
        resp, response_body = self.get('/v1')
        return resp, response_body

    def get_version_v2(self):
        resp, response_body = self.get('/v2')
        return resp, response_body

    def get_backups(self, backup_id=None, **params):

        if backup_id is None:
            uri = '/v2/{0}/backups'.format(self.tenant_id)
            if params:
                uri += '?%s' % urllib.parse.urlencode(params)
        else:
            uri = '/v2/{0}/backups/{1}'.format(self.tenant_id, backup_id)

        resp, response_body = self.get(uri)
        return resp, json.loads(response_body)

    def post_backups(self, metadata, backup_id=None):
        uri = '/v2/{0}/backups'.format(self.tenant_id)
        if backup_id is not None:
            uri += '/' + backup_id

        request_body = json.dumps(metadata)
        resp, response_body = self.post(uri, request_body)

        return resp, json.loads(response_body)

    def delete_backups(self, backup_id):

        uri = '/v2/{0}/backups/{1}'.format(self.tenant_id, backup_id)
        resp, response_body = self.delete(uri)
        return resp, response_body

    def get_clients(self, client_id=None, **params):

        if client_id is None:
            uri = '/v2/{0}/clients'.format(self.tenant_id)
            if params:
                uri += '?%s' % urllib.parse.urlencode(params)

        else:
            uri = 'v2/{0}/clients/{1}'.format(self.tenant_id, client_id)

        resp, response_body = self.get(uri)
        return resp, response_body

    def post_clients(self, client):

        request_body = json.dumps(client)
        resp, response_body = self.post('/v2/{0}/clients'.format(
            self.tenant_id), request_body)
        return resp, json.loads(response_body)

    def delete_clients(self, client_id):

        uri = '/v2/{0}/clients/{1}'.format(self.tenant_id, client_id)
        resp, response_body = self.delete(uri)
        return resp, response_body

    def get_jobs(self, job_id=None, **params):

        if job_id is None:
            uri = '/v2/{0}/jobs'.format(self.tenant_id)
            if params:
                uri += '?%s' % urllib.parse.urlencode(params)
        else:
            uri = '/v2/{0}/jobs/{1}'.format(self.tenant_id, job_id)

        resp, response_body = self.get(uri)
        return resp, response_body

    def post_jobs(self, job):

        request_body = json.dumps(job)
        resp, response_body = self.post('/v2/{0}/jobs'.format(
            self.tenant_id), request_body)
        return resp, json.loads(response_body)

    def delete_jobs(self, job_id):

        uri = '/v2/{0}/jobs/{1}'.format(self.tenant_id, job_id)
        resp, response_body = self.delete(uri)
        return resp, response_body

    def get_actions(self, action_id=None, **params):

        if action_id is None:
            uri = '/v2/{0}/actions'.format(self.tenant_id)
            if params:
                uri += '?%s' % urllib.parse.urlencode(params)
        else:
            uri = '/v2/{0}/actions/{1}'.format(self.tenant_id, action_id)

        resp, response_body = self.get(uri)
        return resp, response_body

    def post_actions(self, action, action_id=None):

        request_body = json.dumps(action)

        if action_id is None:
            uri = '/v2/{0}/actions'.format(self.tenant_id)
        else:
            uri = '/v2/{0}/actions/{1}'.format(self.tenant_id, action_id)

        resp, response_body = self.post(uri, request_body)
        return resp, json.loads(response_body)

    def patch_actions(self, action, action_id):

        request_body = json.dumps(action)

        uri = '/v2/{0}/actions/{1}'.format(self.tenant_id, action_id)
        resp, response_body = self.patch(uri, request_body)
        return resp, json.loads(response_body)

    def delete_actions(self, id):

        uri = '/v2/{0}/actions/{1}'.format(self.tenant_id, id)
        resp, response_body = self.delete(uri)
        return resp, response_body

    def get_sessions(self, session_id=None, **params):

        if session_id is None:
            uri = '/v2/{0}/sessions'.format(self.tenant_id)
            if params:
                uri += '?%s' % urllib.parse.urlencode(params)
        else:
            uri = '/v2/{0}/sessions/'.format(self.tenant_id, session_id)

        resp, response_body = self.get(uri)
        return resp, response_body

    def post_sessions(self, session):

        request_body = json.dumps(session)
        resp, response_body = self.post('/v2/{0}/sessions'.format(
            self.tenant_id), request_body)
        return resp, json.loads(response_body)

    def delete_sessions(self, session_id):

        uri = '/v2/{0}/sessions/{1}'.format(self.tenant_id, session_id)
        resp, response_body = self.delete(uri)
        return resp, response_body
