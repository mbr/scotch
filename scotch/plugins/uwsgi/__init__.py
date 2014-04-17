from pathlib import Path
import subprocess

from scotch.app import WSGIApp
from scotch.plugins import Plugin


class UWSGIPlugin(Plugin):
    def generate_uwsgi_config(self, app):
        """Generates the necessary UWSGI configuration for the app."""
        output_fn = Path(app.config['uwsgi']['app_config'])

        kwargs = {}

        if app.config['uwsgi'].getboolean('drop_root'):
            kwargs['uid'] = app.uid
            kwargs['gid'] = app.gid

        self.output_template('app.ini', output_fn, config=app.config,
                             _mode=int(app.config['uwsgi']['config_mode'], 8),
                             **kwargs)

    def activate_uwsgi_config(self, app):
        link = Path(app.config['uwsgi']['app_enabled_link'])

        if not link.parent.exists():
            self.log.warning('Creating non-existant {}'.format(link.parent))
            link.parent.mkdir(parents=True)

        self.log.info('Creating link {}'.format(link))

        if link.exists():
            link.unlink()
        link.symlink_to(Path(app.config['uwsgi']['app_config']))

        # reload uwsgi
        subprocess.check_call([app.config['uwsgi']['reload_command']],
                              shell=True)

    def enable_app(self, app):
        WSGIApp.register.exit.connect(self.generate_uwsgi_config)
        WSGIApp.activate.exit.connect(self.activate_uwsgi_config)


plugin = UWSGIPlugin
