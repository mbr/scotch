from argparse import ArgumentParser
import os
import subprocess

import logbook
from logbook import Logger, StderrHandler, NullHandler

from scotch.app import Site


def main_scotch_deploy():
    log = Logger('main')

    parser = ArgumentParser()
    parser.add_argument('-c', '--configuration-file',
                        action='append', default=[],
                        help='Configuration files to search. Can be given '
                             'multiple times, default is {!r}'
                             .format(Site.DEFAULT_CONFIGURATION_PATHS))
    parser.add_argument('-d', '--debug', default=False, action='store_true')
    subparsers = parser.add_subparsers(dest='action',
                                       help='Action to perform')

    cmd_list = subparsers.add_parser('list', help='List available apps')

    cmd_deploy = subparsers.add_parser('deploy', help='Deploy app')
    cmd_deploy.add_argument('app_name', nargs='+')
    cmd_dump = subparsers.add_parser('dump', help='Dump app configuration')
    cmd_dump.add_argument('app_name', nargs='+')

    args = parser.parse_args()

    # set up logging handlers
    if not args.debug:
        NullHandler(level=logbook.DEBUG).push_application()
        handler = StderrHandler(level=logbook.INFO)
        handler.format_string = '{record.message}'
        handler.push_application()


    wd = Site(args)

    # set site-umask
    umask = int(wd.config['site']['umask'], 8)
    log.debug('Setting umask to {:04o}'.format(umask))
    os.umask(umask)

    def _header(s):
        print(s)
        print('=' * len(s))

    # commands:
    def list():
        wd.load_apps()

        for name, app in sorted(wd.apps.items()):
            print(name)
            for domain in sorted(app.domains):
                print('  {}{}'.format(domain, app.url_prefix))

    def deploy():
        for name in args.app_name:
            app = wd.load_app(name)
            app.deploy()

    def dump():
        for name in args.app_name:
            app = wd.load_app(name)
            app.config['app']['instance_id'] = '(INSTANCE_ID)'

            # dump config
            _header('App configuration for {}'.format(name))
            for section_name, section in sorted(app.config.items()):
                for key, value in sorted(section.items()):
                    print('{}:{} = {!r}'.format(section_name, key,  value))
                print

    # call appropriate command
    try:
        locals()[args.action]()
    except subprocess.CalledProcessError as e:
        log.critical('Command failed: {}'.format(' '.join(e.cmd)))
