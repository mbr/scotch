import os
from logbook import Logger
import subprocess
from wsgideploy.app import WSGIApp

log = Logger('git')

def register(deploy):
    pass


@WSGIApp.checked_out_source.connect
def check_out_repo(sender, src_path):
    log.info('Checkout using git')
    git_args = ['git', 'archive', '--format', 'tar']

    src = sender.config['src']
    if not '://' in src:
        src = os.path.expanduser(src)
    git_args.extend(['--remote' ,src])
    git_args.append(sender.config.get('git.branch', 'master'))

    # create destination directory
    os.makedirs(src_path)

    # start untarring-process
    tarproc = subprocess.Popen(['tar', '-xf', '-'], cwd=src_path,
                                    stdin=subprocess.PIPE)

    log.debug('Exporting git repository {} to '.format(src, src_path))

    subprocess.check_call(git_args, stdout=tarproc.stdin)

    if not tarproc.wait() == 0:
        raise RuntimeError('tar failed')
