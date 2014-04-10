from os.path import expanduser
import subprocess

from pathlib import Path

from wsgideploy.plugins import Plugin


class GitPlugin(Plugin):
    def check_out_repo(self, app):
        src_path = Path(app.config['app']['src_path'])
        self.log.info('Checkout using git')
        git_args = ['git', 'archive', '--format', 'tar']

        src = app.config['app']['src']
        if not '://' in src:
            src = expanduser(src)
        git_args.extend(['--remote', src])
        git_args.append(app.config['git']['branch'])

        # start untarring-process
        tarproc = subprocess.Popen(['tar', '-xf', '-'],
                                   cwd=str(src_path),
                                   stdin=subprocess.PIPE)

        self.log.debug('Exporting git repository {} to '.format(src,
                                                                src_path))

        subprocess.check_call(git_args, stdout=tarproc.stdin)

        if not tarproc.wait() == 0:
            raise RuntimeError('tar failed')

    def enable_app(self, app):
        app.checked_out_source.connect(self.check_out_repo)

plugin = GitPlugin
