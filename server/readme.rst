Status Servers
==============

This directory contains the two status servers that I have used with
the pager.

Google App Engine server
------------------------

The server in the ``gae/`` directory is an app engine program.
AppEngine is very cheap and Google will automatically scale your
program across machines.  The original code contained embedded
constants, so you will need to set the appropriate variables::

  server/gae/main.py capability = the 'token': x field
                                  from client pagerrc.json

  server/gae/main.py status_cap = the ?token= used to observe the status

  server/gae/over.py API_TOKEN = the application's pushover api token

  server/gae/over.py GROUP_TOKEN = the pushover group to send alert
                                   messages to

After setting up a google cloud account and installing the python SDK,
you can run it with::

  dev_appserver.py app.yaml

You can deploy the app to your google appengine cloud with::

  gcloud app deploy

Docker Server
-------------

The server in the ``docker/`` directory is based on twisted python and
sqlalchemy and is much easier to build and set up.  The
``build-application.sh`` script in this directory can run the commands
to build the docker instance required.  After it has completed, it
will give you an example command that you can run to start the server
in docker yourself.

This version of the application lacks the database cleaning features
of the GAE server.  Nevertheless, it is a standalone application that
does not require a google environment.

This server places its data into the ``pager-data`` volume.  This
volume is expected to be configured with a ``pager_config.json`` file.
An example configuration is included, but a more secure configuration
should be provided.  The ``_max`` configuration variables are ignored
in this version.  The api and group tokens are for the use of
pushover, as described in the GAE section.  The service capability is
the token that appears in the pagerrc.json file on the pi, wheras the
status capability is the token passed to the web page to view the
status of the devices.

This server has integration tests.  One way to run them, assuming you
are in ``server/docker/`` is::

  pypy -m pip install pytest
  pypy -m pip install -r requirements.txt
  pypy -m pytest .

Integration testing
-------------------

There is a mock pager at ``./fakerpi``.  Run either of the pager
servers, and then run fakerpi with ``./fakerpi --local`` to start
sending pager data at the server.  An example alert message is
provided.
