WSGI-deployment made easy
=========================

wsgi-deploy is a toolkit to deploy many small WSGI-applications onto a
single server. It will allow you to specify how an app should be deployed
and generate nginx, uwsgi-configuration files and virtualenvs.


Configuration file syntax
-------------------------

Here is an example configuration file (JSON-syntax), ``sample-app.conf``:

  {
    'source-uri': 'git://somehost:/some/repo',
    'app-factory': 'sampleapp.create_app',
  }

Running ``wsgi-deploy myapp`` will cause wsgi-deploy to:

1. Create a new home for the application (in ``/srv/wsgi-apps/sample-app-ID``).
   ``ID`` is a random id that gets generated with each instance,
   to allow seamless switching over in production.
2. Create a new virtualenv in ``/src/wsgi-apps/sample-app-ID/venv``.
3. Checkout the git repository to ``/src/wsgi-apps/sample-app-ID/app``.
4. Install all of the requirements through ``requirements.txt`` found in the
   app; if none is found there, run ``python setup.py develop``.
5. Create a configuration file by merging all of ``conf/*`` in canonical order
   into a larger file, stored in ``/src/wsgi-apps/sample-app-ID/config``.
6. Generate the necessary application server configuration (usually uwsgi).
7. Generate the necessary nginx server configuration.
8. Reload the application server.
9. Reload the webserver.


Global configuration
--------------------

Global configuration for wsgi-deploy is merged, in the following order:

1. Built-in defaults (shipped as ``wsgi-deploy/defaults.conf``).
2. ``/etc/wsgi-deploy.conf``
3. ``~/wsgi-deploy.conf``
4. ``./wsgi-deploy.conf``.

Generation of configuration is handled through plugins,
two are shipped with wsgi-deploy: ``nginx`` for webserver deployments and
``uwsgi`` as the application server.

Sample configuration:

  {
    'python-version': null,
    'nginx.sites-available': '/etc/nginx/sites-available',
    'nginx.sites-enabled': '/etc/nginx/sites-enabled',
    'nginx.reload-command': '/etc/init.d/nginx reload',
    'uwsgi.reload-command': '/etc/init.d/uwsgivirtual reload',
  }
