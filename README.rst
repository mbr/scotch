WSGI-deployment made easy
=========================

scotch is a toolkit to deploy many WSGI-applications onto a single server.
It will allow you to specify how an app should be deployed
and generate nginx, uwsgi-configuration files and virtualenvs.


Quick start
~~~~~~~~~~~

First, install scotch (preferably on a Debian or Ubuntu system). Then create
a file named ``/etc/scotch/apps-enabled/dram.cfg`` as follows::

    [app]
    src=git@github.com:mbr/scotch-sample-app


Now simply run (as root)::

    $ scotch deploy dram

after which the sample app should greet you at http://localhost. See the
`source <https://github .com/mbr/scotch-sample-app>`_ of the sample
application for some ideas on how an app can be configured.


Operation overview
------------------

First, scotch is set up on the system by providing a suitable global
configuration, called the site configuration. The shipped default is
suitable for Debian stable and Ubuntu LTS deployments,
other distros may need different settings.

In theory multiple application and webservers are supported through the
plugin architecture, however currently scotch ships only with  `nginx
<http://nginx.org>`_ and `uWSGI <http://projects.unbit.it/uwsgi/>`_
support, so make sure these are installed.

Apps
~~~~

Each app has its own configuration configuration file,
found at /etc/scotch/apps-enabled. Deploying an app is done by
triggering the two-step deployment process by running::

   $ scotch deploy myapp


The first step is called **checkout**. A new *instance* of the app will be
created (per default in ``/var/local/scotch/appname``). An instance is a
directory that contains (almost) all of the deployment.

The application's source code is copied into the source dir at
instance_dir/``src``. The default source is a git repository,
however the resulting copy will just be a plain directory.

Afterwards a new `virtualenv <https://pypi.python.org/pypi/virtualenv>`_ is
created and dependencies of the app are installed.

Now that that it is runnable, the app will **register** as the second step;
i.e. the configuration files for web and application servers will be
generated and the affected servers will be reloaded or restartet.
Afterwards, the app is live.

When using nginx and uwsgi, you can check the ``sites-enabled`` and
``scotch-apps`` subdirectories of ``/etc/nginx/`` for nginx configuration,
as well as ``/etc/uwsgi/apps-enabled`` for the uwsgi ini files created.


Configuration files
-------------------

Configuration files for scotch are loaded in the following order for each app
instance. Files loaded later can overwrite values from files loaded earlier:

1. Built-in defaults (for scotch and plugins).
2. Site configuration: ``./scotch.cfg``, ``~/.scotch.cfg`` and
   ``/etc/scotch.cfg``. These locations can be overridden by the ``-c``
   command line option, which is helpful for non-root testing.
3. App configuration, in ``/etc/scotch/apps.enabled/myapp.cfg`` (for an app
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
between different distributions and web or application servers.

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

Each app configuration can override any option of the configuration,
however most often those in the [app] section are overriden. See the
defaults file (https://github.com/mbr/scotch/blob/master/scotch/defaults.cfg)
for commented options.
