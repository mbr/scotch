WSGI-deployment made easy
=========================

scotch is a toolkit to deploy many WSGI-applications onto a single server.
It will allow you to specify how an app should be deployed
and generate nginx, uwsgi-configuration files and virtualenvs.


Operation overview
------------------

First, scotch is set up on the system by providing a suitable global
configuration, called the site configuration. Different ways of deploying
apps are supported, the shipped defaults assume a Debian system using `nginx
 <http://nginx.org>`_ and `uWSGI <http://projects.unbit.it/uwsgi/>`_.

Every app also adds its own configuration options as needed,
stored in a different configuration file. Deploying an app is done by
running::

   $ scotch deploy myapp

This will trigger a three-step process:

1. A new *instance* of the app will be created. An instance is a directory
   that contains (almost) all of the necessary information for the
   deployment.
2. The app will be *checked out* into the instance from a VCS,
   archive or some other source.
3. A new `virtualenv <https://pypi.python.org/pypi/virtualenv>`_ will be
   created and dependencies of the app will be installed.
4. Finally, the app will be *registered*. This is site dependant and handled
   by plugins that can, for example, generate configuration files for
   webservers or wsgi application servers.


Configuration files
-------------------

Configuration files are loaded in the following order for each app instance.
Files loaded later can overwrite values from files loaded earlier:

1. Built-in defaults (for scotch and plugins).
2. Site configuration: ``./scotch.cfg``, ``~/.scotch.cfg`` and
   ``/etc/scotch.cfg``. These locations can be overridden by the ``-c``
   command line option.
3. App configuration, in ``/etc/scotch/apps.enabled/myapp`` (for an app
   named "myapp"). This path is configurable as ``${paths:configuration}``
   (see below).


Configuration file syntax
~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration files use the ``configparser`` module `found in the Python 3
stdlib <https://docs.python.org/3.3/library/configparser.html>`_ or `its
backport <https://pypi.python.org/pypi/configparser>`_ on Python 2. The
`extended interpolation <https://docs.python.org/3.3/library/configparser.html
#configparser.ExtendedInterpolation>`_ is also used.


Site configuration
~~~~~~~~~~~~~~~~~~

The site configuration is meant to be used to smooth away differences
between different distributions and web or application servers. Ideally,
no changes will have to be made because the defaults are fairly reasonable
on Debian-based systems.

For educational purposes, here is an example for a more exotic
``/etc/scotch.cfg``::

    [app]
    interpreter=/usr/local/custom-python/bin/python
    venv_path=/virtualenvs/${name}

    [paths]
    configuration=/nfs/conf/scotch
    instances=/nfs/scotch-instances


This will enables a custom compiled interpreter and configuration and
instances store on an (assumed) nfs volume, while virtual environments are
kept on the local machine. Note that configuration files are just merged
together, there's no technical distinction between a defaults-file,
site configuration or app configuration.


App configuration
~~~~~~~~~~~~~~~~~

Configuration for an application is read from ``${app:config}``, which will
per default end up as ``/etc/scotch/apps.enabled/dram.cfg`` for an app named
``dram``. Here is an example::

    [app]
    source_type=git
    src=git@github.com:mbr/scotch-sample-app


If you create the above file with the name specified, you can run::

    $ scotch deploy dram

which should just work. See the `source <https://github
.com/mbr/scotch-sample-app`_ of the sample application for details on how an
app should be configured.
