from functools import wraps, partial
from grp import getgrnam
from importlib import import_module
import os
from os.path import expanduser
from pwd import getpwnam
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


def signalling(f):
    """Adds an .enter and .exit signal to a method, which are emitted upon
    entry/exit from a method call. Sender is the object itself."""
    f.enter = Signal('{}.enter'.format(f.__name__))
    f.exit = Signal('{}.exit'.format(f.__name__))

    @wraps(f)
    def _(self, *args, **kwargs):
        log.debug('Enter {}:{}'.format(self.name, f.__name__))
        f.enter.send(self)
        rv = f(self, *args, **kwargs)
        f.exit.send(self)
        log.debug('Finished {}:{}'.format(self.name, f.__name__))
        return rv

    return _


def drop_root(uid=None, gid=None):
    """Drops root permissions by changing to a different UID and GID.

    :param uid: numeric user id to change to. May be ``None`` to ignore.
    :param gid: numeric group id to change to. May be ``None`` to ignore."""
    if gid:
        os.setgid(gid)
    if uid:
        os.setuid(uid)


def chown(path, uid=None, gid=None):
    """Changes ownership of target path.

    :param uid: new uid for file (-1 to ignore).
    :param gid: new gid for file (-1 to ignore)."""

    if uid is None:
        uid = -1

    if gid is None:
        gid = -1

    if uid != -1 or gid != -1:
        log.debug('Changing ownership of {} to {}:{}'.format(
            path, uid, gid)
        )

        os.chown(str(path), uid, gid)


class WSGIApp(object):
    request_source = Signal()

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
        #  always active)
        for plugin in site.plugins.values():
            plugin.enable_app(self)

    @property
    def dirmode(self):
        return int(self.config['site']['dirmode'], 8)

    @property
    def uid(self):
        if self.config['app']['user']:
            return getpwnam(self.config['app']['user']).pw_uid

    @property
    def gid(self):
        if self.config['app']['user']:
            return getgrnam(self.config['app']['group']).gr_gid

    @property
    def domains(self):
        return [d.strip() for d in self.config['app']['domains'].split()]

    @property
    def url_prefix(self):
        return self.config['app']['url_prefix']


    def command_args(self, drop_root=False, **kwargs):
        kwargs.setdefault('stderr', subprocess.STDOUT)

        # use a (mostly) clean environment
        env = {
            'PATH': os.environ['PATH'],
        }

        rv= {
            'close_fds': True,
            'env': env,
        }

        if drop_root:
            rv['preexec_fn'] = partial(drop_root, self.uid, self.gid),

        rv.update(kwargs)
        return rv

    def run_command(self, *args, **kwargs):
        kwargs = self.command_args(**kwargs)

        try:
            log.debug('Running subprocess: {!r} {!r}'.format(args, kwargs))
            return subprocess.check_output(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            log.debug(e.output)
            raise


    def chown_to_user(self, path):
        chown(path, self.uid, self.gid)

    @signalling
    def checkout(self):
        # generate an instance-id and app directory
        self.config['app']['instance_id'] = shortuuid.uuid()

        # create instance folder
        # note: instance folder is owned by root and read-only
        instance_path = Path(self.config['app']['instance_path'])
        instance_path.mkdir(self.dirmode, parents=True)

        log.info('Instance path is {}'.format(instance_path))

        # create run_path
        run_path = Path(self.config['app']['run_path'])
        run_path.mkdir(self.dirmode, parents=True)

        # make the run-path owned by the application/web user
        self.chown_to_user(run_path)

        # prepare virtualenv
        log.info('Creating new virtualenv')
        venv_path = Path(self.config['app']['venv_path'])
        log.debug('virtualenv based in {}'.format(venv_path))

        venv_path.mkdir(self.dirmode, parents=True)
        venv_args = ['virtualenv', '--distribute']

        interpreter = self.config['app']['interpreter']
        if interpreter is not None:
            venv_args.extend(['-p', interpreter])

        venv_args.append(str(venv_path))

        # we use subprocess rather than the API because we may need to use a
        # different python interpreter
        # note that the virtualenv is read-only
        self.run_command(venv_args)

        src_path = Path(self.config['app']['src_path'])
        src_path.mkdir(self.dirmode, parents=True)
        log.info('Checking out source {}'.format(self.config['app']['src']))
        log.debug('Checkout path is {}'.format(src_path))

        self.request_source.send(self)

        # install requirements
        requirements = src_path / 'requirements.txt'
        pip = venv_path / 'bin' / 'pip'

        if requirements.exists():
            log.info('Installing dependencies using pip/requirements.txt')
            self.run_command([str(pip), 'install', '-r', str(requirements)])
        else:
            log.debug('{} not found, using setup.py develop'.format(
                requirements))

            log.info('Installing package (and dependencies) using pip')
            self.run_command(
                [str(pip), 'install', '.'],
                cwd=str(src_path)
            )

    @signalling
    def activate(self):
        pass

    @signalling
    def deploy(self):
        log.info('Deploying {}...'.format(self.name))

        self.checkout()
        self.activate()


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
        for name in cfg['plugins']:
            if not cfg['plugins'].getboolean(name):
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
        for p in sorted(Path(self.config['paths']['apps_enabled']).iterdir()):
            self.load_app(p.stem)

    @property
    def global_configuration_files(self):
        """Returns paths for configuration files to be parsed. 2-Tuple,
        first a path for the default values, then a list of global
        configuration files."""
        return
