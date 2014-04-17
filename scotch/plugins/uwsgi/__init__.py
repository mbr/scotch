from pathlib import Path
import subprocess

from scotch.app import WSGIApp
from scotch.plugins import Plugin


class UWSGIPlugin(Plugin):
    def activate_uwsgi_config(self, app):
        """Generates the necessary UWSGI configuration for the app."""
        output_fn = Path(app.config['uwsgi']['app_config'])

        kwargs = {}

        self.output_template('app.ini', output_fn, config=app.config,
                             _mode=int(app.config['uwsgi']['config_mode'], 8),
                             **kwargs)

        # reload uwsgi
        subprocess.check_call([app.config['uwsgi']['reload_command']],
                              shell=True)

    def enable_app(self, app):
        WSGIApp.activate.exit.connect(self.activate_uwsgi_config)


plugin = UWSGIPlugin
