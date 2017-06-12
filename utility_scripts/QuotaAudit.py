# Copyright 2017 Massachusetts Open Cloud
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# cleaunder the License.

# import ConfigParser
import os
from keystoneclient.v3 import client
from keystoneauth1 import session
from keystoneauth1.identity import v2
from keystoneauth1.exceptions.http import NotFound
from neutronclient.v2_0 import client as nclient
from novaclient import client as novaclient
from cinderclient.v2 import client as cinderclient

# Use only one of the auth sections below

"""
# Uncomment this section to authenticate with a config file
#CONFIG_FILE = '/path/to/file'
#config = ConfigParser.ConfigParser()
#config.read(CONFIG_FILE)
#admin_user = config.get('auth', 'admin_user')
#admin_pwd = config.get('auth', 'admin_pwd')
#admin_project = config.get('auth', 'admin_project')
#auth_url = config.get('auth', 'auth_url')
"""

# Uncomment this section to authenticate with an environment set from a
# keystonerc file
admin_user = os.environ.get('OS_USERNAME')
admin_pwd = os.environ.get('OS_PASSWORD')
admin_project = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')

"""
# Uncomment this section to authenticate with hard coded values
#admin_user = 'admin'
#admin_pwd = 'secret'
#admin_project = 'admin'
#auth_url = 'http://some-auth-url'
"""

auth = v2.Password(auth_url=auth_url,
                   username=admin_user,
                   password=admin_pwd,
                   tenant_name=admin_project)

sess = session.Session(auth=auth)
keystone = client.Client(session=sess)
ks_projects = keystone.projects.list()
neutron = nclient.Client(session=sess)
nova = novaclient.Client(2, session=sess)
cinder = cinderclient.Client(session=sess)

moc_standards = {'subnet': 10, 'router': 10, 'port': 10, 'network': 5,
                 'floatingip': 2, 'security_group': -1,
                 'security_group_rule': -1, 'ram': 51200, 'gigabytes': 1000,
                 'snapshots': 10, 'volumes': 10,
                 'injected_file_content_bytes': 10240, 'injected_files': 5,
                 'metadata_items': 128, 'instances': 10, 'cores': 20}


def diff_moc_quotas(project_quotas):

    different_quotas = {}
    for each_quota in moc_standards:
        if moc_standards[each_quota] == project_quotas[each_quota]:
            continue
        else:
            different_quotas[each_quota] = project_quotas[each_quota]
    return different_quotas


def to_single_dict(no_q, ci_q, ne_q):

    combined = {}
    combined.update(no_q)
    combined.update(ci_q)
    combined.update(ne_q)
    return combined


all_neutron_quotas = [q for q in neutron.list_quotas()['quotas']]
for qset in all_neutron_quotas:
    proj_id = qset['tenant_id']

    try:
        project = keystone.projects.get(proj_id)
        nova_quotas = nova.quotas.get(proj_id).to_dict()
        cinder_quotas = cinder.quotas.get(proj_id).to_dict()
        combined_quotas = to_single_dict(nova_quotas, cinder_quotas, qset)

        if diff_moc_quotas(combined_quotas):
            print project
            print "Unique Project Quotas:", diff_moc_quotas(combined_quotas)

    except NotFound:
        # it seems when projects are deleted their quota sets are not ?
        print "%s not found" % proj_id
