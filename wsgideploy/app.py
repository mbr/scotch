from importlib import import_module
import os
import subprocess

from blinker import Signal

from logbook import Logger
import shortuuid


log = Logger('WSGIDeploy')


class WSGIApp(object):
    checking_out_source = Signal()

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

    def check_call(self, *args, **kwargs):
        kwargs.setdefault('stderr', subprocess.STDOUT)

        try:
            log.debug('Running subprocess: {!r} {!r}'.format(args, kwargs))
            return subprocess.check_output(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            log.debug(e.output)
            raise

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

        venv_args = ['virtualenv', '--distribute']

        python_version = self.config.get('python-version', None)
        if python_version is not None:
            venv_args.extend(['-p', python_version])

        venv_args.append(venv_path)

        # we use subprocess rather than the API because we may need to use a
        # different python interpreter
        log.debug(venv_args)
        self.check_call(venv_args)

        src_path = self.get_instance_path(self.config['instance-src-dir'])
        log.debug('Requesting new source checkout into {}'.format(src_path))

        # signal source plugin to check out
        self.checking_out_source.send(self, src_path=src_path)

        # install requirements
        requirements = self.get_instance_path(
            self.config['instance-src-dir'], 'requirements.txt')

        python = self.get_instance_path(
            self.config['instance-venv-dir'], 'bin', 'python')

        pip = self.get_instance_path(
            self.config['instance-venv-dir'], 'bin', 'pip')

        if os.path.exists(requirements):
            self.check_call(['pip', 'install', '-r', requirements])
        else:
            log.debug('{} not found, using setup.py develop'.format(
                requirements))

            self.check_call(
                [pip, 'install', '.'],
                cwd=self.get_instance_path(self.config['instance-src-dir'])
            )


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
