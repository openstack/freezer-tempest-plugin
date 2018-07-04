====================
Enabling in Devstack
====================

**WARNING**: the stack.sh script must be run in a disposable VM that is not
being created automatically, see the README.md file in the "devstack"
repository.

1. Download DevStack::

    git clone https://git.openstack.org/openstack-dev/devstack.git
    cd devstack

2. Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin freezer-tempest-plugin https://git.openstack.org/openstack/freezer-tempest-plugin

3. run ``stack.sh``

Running Freezer tempest tests
=============================

1. Listing Freezer tempest tests::

    tempest list-plugins

2. Running freezer tempest tests::

    cd /opt/stack/tempest
    tempest run -r freezer_tempest_test
