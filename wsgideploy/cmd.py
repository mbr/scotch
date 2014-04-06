from argparse import ArgumentParser
from importlib import import_module
import os
import subprocess

from .defaults import cfg as default_config
from .config import ConfigDict

from logbook import Logger
from wsgideploy.app import WSGIDeploy


DEFAULT_CONFIGURATION_PATHS=[
    '/etc/wsgi-deploy.conf'
    '~/.wsgi-deploy.conf',
    './wsgi-deploy.conf',
]


def main_wsgi_deploy():
    log = Logger('main')

    parser = ArgumentParser()
    parser.add_argument('-c', '--configuration-file',
                        action='append', default=[],
                        help='Configuration files to search. Can be given '
                             'multiple times, default is {!r}'
                             .format(DEFAULT_CONFIGURATION_PATHS))
    subparsers = parser.add_subparsers(dest='action',
                                       help='Action to perform')

    cmd_list = subparsers.add_parser('list', help='List available apps')
    cmd_deploy = subparsers.add_parser('deploy', help='Deploy app')

    cmd_deploy.add_argument('app_name')

    args = parser.parse_args()
    if not args.configuration_file:
        args.configuration_file = DEFAULT_CONFIGURATION_PATHS

    # parse configuration
    cfg = ConfigDict(default_config)
    log.debug('Loading configuration from {}'.format(args.configuration_file))
    cfg.load_files(args.configuration_file)

    wd = WSGIDeploy(cfg, args)

    def list():
        wd.load_apps()

        for name in sorted(wd.apps.keys()):
            print(name)

    def deploy():
        app = wd.load_app(args.app_name)

        app.deploy()

    try:
        locals()[args.action]()
    except subprocess.CalledProcessError as e:
        log.critical('Command failed: {}'.format(' '.join(e.cmd)))
