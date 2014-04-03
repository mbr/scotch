from argparse import ArgumentParser
import os
from .config import load_config
from .defaults import cfg as default_config

DEFAULT_CONFIGURATION_PATHS=[
    './wsgi-deploy.conf',
    '~/.wsgi-deploy.conf',
    '/etc/wsgi-deploy.conf'
]


def main_wsgi_deploy():
    parser = ArgumentParser()
    parser.add_argument('-c', '--configuration-file',
                        action='append', default=[],
                        help='Configuration files to search. Can be given '
                             'multiple times, default is {!r}'
                             .format(DEFAULT_CONFIGURATION_PATHS))
    args = parser.parse_args()
    if not args.configuration_file:
        args.configuration_file = DEFAULT_CONFIGURATION_PATHS

    cfg = load_config(args.configuration_file, default_config)
    print cfg
