import jinja2
from logbook import Logger
from pathlib import Path
from wsgideploy.app import WSGIApp
from wsgideploy.plugins import Plugin


class UWSGIPlugin(Plugin):
    @WSGIApp.deployed_app.connect
    def generate_uwsgi_config(self, app):
        output_fn = (Path(app.config['uwsgi']['apps_available_path'])
                     / '{}.ini'.format(app.name))

        self.output_template('app.ini', output_fn)


plugin = UWSGIPlugin
