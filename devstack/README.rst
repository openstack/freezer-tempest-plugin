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
    cd devstack/tools
    ./create_stack_user
    
    cd devstack
    chown -R stack ./devstack/


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

     #export FREEZER_BACKEND='sqlalchemy'

4. Use stack user to run ``stack.sh``
    su stack
    ./stack.sh
    

Running Freezer tempest tests
=============================

1. Listing Freezer tempest tests::

    tempest list-plugins

2. Running freezer tempest tests::

    cd /opt/stack/tempest
    tempest run -r freezer_tempest_test
