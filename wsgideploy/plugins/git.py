import os
from logbook import Logger
import subprocess
from wsgideploy.app import WSGIApp

log = Logger('git')

def register(deploy):
    pass


@WSGIApp.checking_out_source.connect
def check_out_repo(sender, src_path):

    git_args = ['git', 'clone']

    src = sender.config['src']
    if not '://' in src:
        src = os.path.expanduser(src)
    git_args.append(src)
    git_args.append(src_path)

    branch = sender.config.get('git.branch', None)
    if branch:
        git_args.extend(['--branch', branch])

    log.debug('Checking out git repository: {} to {}'.format(src, src_path))

    sender.check_call(git_args)
