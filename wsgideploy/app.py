from importlib import import_module
import os
from os.path import expanduser
import subprocess

from blinker import Signal
from configparser import ConfigParser, ExtendedInterpolation
from logbook import Logger
from pathlib import Path
import shortuuid


log = Logger('WSGIDeploy')


class WSGIApp(object):
    checked_out_source = Signal()
    deployed_app = Signal()

    def __init__(self, name, deploy):
        # load configuration, starting from global and reading app sepcific
        self.config = deploy.load_config()
        self.name = name

        # set application name
        self.config['app']['name'] = name

        # find configuration file
        cfgfile = Path(self.config['app']['config_file'])
        if not cfgfile.exists():
            log.debug('Missing {}'.format(cfgfile))
            raise RuntimeError('Configuration file {} missing for app {}'
                               .format(cfgfile, name))

        # load configuration
        log.debug('Loading app configuration for {}'.format(name))

        self.config.read_file(cfgfile.open())


    def check_output(self, *args, **kwargs):
        kwargs.setdefault('stderr', subprocess.STDOUT)

        try:
            log.debug('Running subprocess: {!r} {!r}'.format(args, kwargs))
            return subprocess.check_output(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            log.debug(e.output)
            raise


    def deploy(self):
        log.info('Deploying {}...'.format(self.name))

        # generate an instance-id and app directory
        self.instance_id = shortuuid.uuid()

        venv_path = self.get_instance_path(self.config['instance-venv-dir'])
        os.makedirs(venv_path)

        # prepare virtualenv
        log.info('Creating new virtualenv')
        log.debug('virtualenv based in {}'.format(venv_path))

        venv_args = ['virtualenv', '--distribute']

        python_version = self.config.get('python-version', None)
        if python_version is not None:
            venv_args.extend(['-p', python_version])

        venv_args.append(venv_path)

        # we use subprocess rather than the API because we may need to use a
        # different python interpreter
        self.check_output(venv_args)

        src_path = self.get_instance_path(self.config['instance-src-dir'])
        log.info('Checking out source {}'.format(self.config['src']))
        log.debug('Checkout path is {}'.format(src_path))

        # signal source plugin to check out
        self.checked_out_source.send(self, src_path=src_path)

        # install requirements
        requirements = self.get_instance_path(
            self.config['instance-src-dir'], 'requirements.txt')

        python = self.get_instance_path(
            self.config['instance-venv-dir'], 'bin', 'python')

        pip = self.get_instance_path(
            self.config['instance-venv-dir'], 'bin', 'pip')

        if os.path.exists(requirements):
            log.info('Installing dependencies using pip/requirements.txt')
            self.check_output(['pip', 'install', '-r', requirements])
        else:
            log.debug('{} not found, using setup.py develop'.format(
                requirements))

            log.info('Installing package (and dependencies) using pip')
            self.check_output(
                [pip, 'install', '.'],
                cwd=self.get_instance_path(self.config['instance-src-dir'])
            )

        self.deployed_app.send(self)


class WSGIDeploy(object):
    DEFAULT_CONFIGURATION_PATHS=[
        '/etc/wsgi-deploy.cfg'
        '~/.wsgi-deploy.cfg',
        './wsgi-deploy.cfg',
    ]

    def __init__(self, args):
        self.args = args
        self.config = self.load_config()

        self.apps = {}
        self.plugins = {}

        # load plugins
        for name, enabled in self.config['plugins'].items():
            if not enabled:
                continue

            # plugins are loaded by importing a module with the name of
            # wsgideploy.plugins.PLUGIN_NAME and then instantiating the
            # plugin-classed
            mod = import_module('wsgideploy.plugins.{}'.format(name))
            plugin = mod.plugin(self)
            self.plugins[plugin.name] = plugin

    def load_app(self, name):
        path = Path(self.config['paths']['apps_enabled']) / name
        app = WSGIApp(path.name, self)
        self.apps[app.name] = app
        return app

    def load_apps(self):
        for p in Path(self.config['paths']['apps_enabled']).iterdir():
            self.load_app(p.name)

    def load_config(self):
        # parse configuration
        config_files = [Path(__file__).with_name('defaults.cfg')]
        config_files.extend(self.args.configuration_file or
                            self.DEFAULT_CONFIGURATION_PATHS)

        cfg = ConfigParser(interpolation=ExtendedInterpolation())

        for cfgfile in config_files:
            cfgfile = Path(cfgfile)
            if cfgfile.exists():
                cfg.read_file(open(expanduser(str(cfgfile))))

        return cfg
