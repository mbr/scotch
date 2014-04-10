from os.path import expanduser
import subprocess

from pathlib import Path

from wsgideploy.app import WSGIApp
from wsgideploy.plugins import Plugin


class GitPlugin(Plugin):
    @WSGIApp.checked_out_source.connect
    def check_out_repo(self, app, src_path):
        src_path = Path(src_path)
        self.log.info('Checkout using git')
        git_args = ['git', 'archive', '--format', 'tar']

        src = app.config['src']
        if not '://' in src:
            src = expanduser(src)
        git_args.extend(['--remote', src])
        git_args.append(app.config.get('git.branch', 'master'))

        # create destination directory
        src_path.mkdir(parents=True)

        # start untarring-process
        tarproc = subprocess.Popen(['tar', '-xf', '-'], cwd=src_path,
                                        stdin=subprocess.PIPE)

        self.log.debug('Exporting git repository {} to '.format(src,
                                                                src_path))

        subprocess.check_call(git_args, stdout=tarproc.stdin)

        if not tarproc.wait() == 0:
            raise RuntimeError('tar failed')

plugin = GitPlugin
