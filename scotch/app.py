from importlib import import_module
import os
from os.path import expanduser
import subprocess

from blinker import Signal
from configparser import ConfigParser, ExtendedInterpolation
from logbook import Logger
from pathlib import Path
import shortuuid


log = Logger('Site')


class SiteConfigParser(ConfigParser):
    def extend_using(self, *config_files):
        for cfgfile in config_files:
            cfgfile = Path(cfgfile)
            if cfgfile.exists():
                self.read_file(open(expanduser(str(cfgfile))))
                log.debug('Configuration from {}'.format(cfgfile))
            else:
                log.debug('Skipping non-existant {}'.format(cfgfile))


class WSGIApp(object):
    checked_out_source = Signal()
    deployed_app = Signal()

    def __init__(self, name, site):
        # load configuration, starting from global and reading app sepcific
        self.name = name

        self.config = site.create_site_config()

        # set application name
        self.config['app']['name'] = name

        # find app configuration file
        app_config = Path(self.config['app']['config'])
        if not app_config.exists():
            log.debug('Missing {}'.format(app_config))
            raise RuntimeError('Configuration file {} missing for app {}'
                               .format(app_config, self.name))

        # load app configuration
        self.config.extend_using(app_config)

        # activate plugins
        # (currently, there's no way to override the list plugins, all are
        #  always activated)
        for plugin in site.plugins.values():
            plugin.enable_app(self)

    def check_output(self, *args, **kwargs):
        kwargs.setdefault('stderr', subprocess.STDOUT)

        try:
            log.debug('Running subprocess: {!r} {!r}'.format(args, kwargs))
            return subprocess.check_output(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            log.debug(e.output)
            raise

    def deploy(self):
        dirmode = 0o777  # FIXME: review security here
        log.info('Deploying {}...'.format(self.name))

        # generate an instance-id and app directory
        self.config['app']['instance_id'] = shortuuid.uuid()

        # create instance folder
        instance_path = Path(self.config['app']['instance_path'])
        instance_path.mkdir(dirmode, parents=True)

        log.info('Instance path is {}'.format(instance_path))

        # create run_path
        run_path = Path(self.config['app']['run_path'])
        run_path.mkdir(dirmode, parents=True)

        # prepare virtualenv
        log.info('Creating new virtualenv')
        venv_path = Path(self.config['app']['venv_path'])
        log.debug('virtualenv based in {}'.format(venv_path))

        venv_path.mkdir(dirmode, parents=True)

        venv_args = ['virtualenv', '--distribute']

        interpreter = self.config['app']['interpreter']
        if interpreter is not None:
            venv_args.extend(['-p', interpreter])

        venv_args.append(str(venv_path))

        # we use subprocess rather than the API because we may need to use a
        # different python interpreter
        self.check_output(venv_args)

        src_path = Path(self.config['app']['src_path'])
        src_path.mkdir(dirmode, parents=True)
        log.info('Checking out source {}'.format(self.config['app']['src']))
        log.debug('Checkout path is {}'.format(src_path))

        # signal source plugin to check out
        self.checked_out_source.send(self)

        # install requirements
        requirements = src_path / 'requirements.txt'
        pip = venv_path / 'bin' / 'pip'

        if requirements.exists():
            log.info('Installing dependencies using pip/requirements.txt')
            self.check_output(['pip', 'install', '-r', str(requirements)])
        else:
            log.debug('{} not found, using setup.py develop'.format(
                requirements))

            log.info('Installing package (and dependencies) using pip')
            self.check_output(
                [str(pip), 'install', '.'],
                cwd=str(src_path)
            )

        self.deployed_app.send(self)


class Site(object):
    DEFAULT_CONFIGURATION_PATHS=[
        '/etc/scotch.cfg',
        '~/.scotch.cfg',
        './scotch.cfg',
    ]

    DEFAULTS_FILE = Path(__file__).with_name('defaults.cfg')

    def __init__(self, args):
        self.args = args

        self.apps = {}
        self.plugins = {}

        self.config = self.create_site_config()

    def create_site_config(self):
        cfg = SiteConfigParser(interpolation=ExtendedInterpolation())

        # load site defaults
        cfg.extend_using(self.DEFAULTS_FILE)

        # load plugin defaults
        for plugin in self.plugins.values():
            cfg.extend_using(plugin.DEFAULTS_FILE)

        # load site configuration
        site_configs = (self.args.configuration_file or
                        self.DEFAULT_CONFIGURATION_PATHS)
        cfg.extend_using(*site_configs)

        plugins_loaded = False

        # load plugins
        for name, enabled in cfg['plugins'].items():
            if not enabled:
                continue

            if not name in self.plugins:
                # plugins are loaded by importing a module with the name of
                # scotch.plugins.PLUGIN_NAME and then instantiating the
                # plugin-classed
                mod = import_module('scotch.plugins.{}'.format(name))

                plugin = mod.plugin(self)
                self.plugins[name] = plugin
                cfg.extend_using(plugin.DEFAULTS_FILE)

                plugins_loaded = True

        if plugins_loaded:
            # slight hack: reload config, as its currently not possible to
            # tell configparser to merge two configurations without
            # overwriting
            log.debug('Additional plugins have been loaded, reloading '
                      'configuration.')
            return self.create_site_config()

        return cfg

    def load_app(self, name):
        app = WSGIApp(name, self)
        self.apps[app.name] = app

        return app

    def load_apps(self):
        for p in Path(self.config['paths']['apps_enabled']).iterdir():
            self.load_app(p.name)

    @property
    def global_configuration_files(self):
        """Returns paths for configuration files to be parsed. 2-Tuple,
        first a path for the default values, then a list of global
        configuration files."""
        return
