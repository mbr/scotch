cfg = {
    'plugins-enabled': ['git', 'uwsgi'],
    'configuration-path': '/etc/wsgi-deploy',
    'applications-path': '/var/local/wsgi-deploy',

    'app-config-file': 'wsgi-deploy.conf',
    'instance-venv-dir': 'venv',
    'instance-src-dir': 'src',
    'apps-enabled-dir': 'apps.enabled',
    'source-type': 'git'
}
