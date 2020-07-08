====================
Enabling in Devstack
====================

**WARNING**: the stack.sh script must be run in a disposable VM that is not
being created automatically, see the README.md file in the "devstack"
repository.

1. Download DevStack::

    git clone https://git.openstack.org/openstack-dev/devstack.git
    cd devstack

2. Add stack user and change devstack directory user group::
   
    ./create_stack_user.sh
    
    chown -R stack ./devstack/
    chown -R stack.stack ./devstack/


3. Add this repo as an external repository::

     > cat local.conf
     MYSQL_PASSWORD=stack
     RABBIT_PASSWORD=stack
     SERVICE_TOKEN=stack
     ADMIN_PASSWORD=stack
     SERVICE_PASSWORD=stack

     [[local|localrc]]
     enable_plugin freezer-tempest-plugin https://git.openstack.org/openstack/freezer-tempest-plugin
     enable_plugin freezer https://git.openstack.org/openstack/freezer
     enable_plugin freezer-api https://git.openstack.org/openstack/freezer-api.git

     export FREEZER_BACKEND='sqlalchemy'

4. Use stack user to run ``stack.sh``::

    su stack
    ./stack.sh
    
5. You can source openrc in your shell, and then use the openstack command line tool to manage your devstack.::

   souce  /opt/stack/devstack/openrc  admin admin

Running Freezer tempest tests
=============================

1. Listing Freezer tempest tests::

    tempest list-plugins

2. Config the "tempest.conf" file::

    cd /opt/stack/tempest
    tox -e genconfig
    cd /opt/stack/tempest/etc
    cp tempest.conf.sample tempest.conf

3. This is a sample "tempest.conf" file::

    [auth]
    admin_username = admin
    admin_project_name = admin
    admin_password = stack
    admin_domain_name = Default
    [identity]
    uri_v3 = http://172.16.1.108/identity/v3


4. Running freezer tempest tests::

    cd /opt/stack/tempest
    tempest run -r freezer_tempest_plugin

5. Running  one tempest test case::

    cd /opt/stack/tempest
    tempest run  -r  freezer_tempest_plugin.tests.freezer_api.api.test_api_jobs.TestFreezerApiJobs.test_api_jobs_post
   
 For more informatin, see:
    https://docs.openstack.org/devstack/latest/index.html
    https://docs.openstack.org/tempest/latest/
