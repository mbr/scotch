from importlib import import_module
import os

from logbook import Logger
import shortuuid


log = Logger('WSGIDeploy')


class WSGIApp(object):
    def __init__(self, name, deploy):
        self.name = name
        self.config = deploy.config.copy()

        log.debug('Loading app {}'.format(name))
        configfile = self.get_conf_path(self.config['app-config-file'])

        if not os.path.exists(configfile):
            log.debug('Missing {}'.format(os.path.abspath(configfile)))
            raise RuntimeError('Configuration file {} missing for app {}'
                               .format(self.config['app-config-file'], name))

        try:
            self.config.load_file(open(configfile))
        except ValueError as e:
            raise ValueError('Error reading configuration for {}: {}'.format(
                name, e
            ))

    def get_conf_path(self, *args):
        return self.config.get_path(
            'configuration-path', self.config['apps-enabled-dir'], self.name,
            *args
        )

    def get_instance_path(self, *args):
        return self.config.get_path(
            'applications-path', self.name, self.instance_id, *args
        )

    def deploy(self):
        log.info('Deploying {}'.format(self.name))

        # generate an instance-id and app directory
        self.instance_id = shortuuid.uuid()

        venv_path = self.get_instance_path(self.config['instance-venv-dir'])
        os.makedirs(venv_path)

        # prepare virtualenv
        log.debug('Preparing virtualenv in {}'.format(venv_path))


class WSGIDeploy(object):
    def __init__(self, config, args):
        self.config = config
        self.args = args

        self.base_dir = self.config.get_path('configuration-path')
        self.apps_enabled_dir = self.config.get_path(
            'configuration-path', self.config['apps-enabled-dir']
        )

        self.apps = {}

        # load plugins
        for name in self.config['plugins-enabled']:
            mod = import_module('wsgideploy.plugins.{}'.format(name))
            mod.register(self)
            log.debug('Loading plugin {}'.format(name))

    def get_app_path(self, name, *args):
        return self.config.get_path(
            'configuration-path', self.config['apps-enabled-dir'], name, *args
        )

    def load_app(self, name, path=None):
        if not path:
            path = self.get_app_path(name)
        app = WSGIApp(name, self)
        self.apps[name] = app
        return app

    def load_apps(self):
        log.debug('Searching for apps in {}'.format(
            os.path.abspath(self.apps_enabled_dir))
        )

        for name in os.listdir(self.apps_enabled_dir):
            self.load_app(name)
