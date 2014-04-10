from pathlib import Path

from wsgideploy.app import WSGIApp
from wsgideploy.plugins import Plugin


class UWSGIPlugin(Plugin):
    def generate_uwsgi_config(self, app):
        output_fn = Path(app.config['uwsgi']['app_config'])

        self.output_template('app.ini', output_fn)

    def enable_app(self, app):
        WSGIApp.deployed_app.connect(self.generate_uwsgi_config)


plugin = UWSGIPlugin
