from pathlib import Path
import subprocess
from scotch.app import WSGIApp
from scotch.plugins import Plugin


class NginxPlugin(Plugin):
    def generate_nginx_config(self, app):
        """Generates the necessary nginx site configuration for the app."""
        output_fn = Path(app.config['nginx']['app_config'])

        # determine what kind of setup we have
        template = 'root.conf'

        if app.config['nginx']['path'] and app.config['nginx']['path'] != '/':
            template = 'submount.conf'

        self.output_template(template, output_fn, config=app.config,
                             _mode=int(app.config['nginx']['config_mode'], 8))

    def activate_nginx_config(self, app):
        link = Path(app.config['nginx']['app_enabled_link'])

        # FIXME: this is duplicate code from the uwsgi plugin.
        # refactor me!
        if not link.parent.exists():
            self.log.warning('Creating non-existant {}'.format(link.parent))
            link.parent.mkdir(parents=True)

        self.log.info('Creating link {}'.format(link))

        if link.exists():
            link.unlink()
        link.symlink_to(Path(app.config['nginx']['app_config']))

        subprocess.check_call([app.config['nginx']['reload_command']],
                              shell=True)

    def enable_app(self, app):
        WSGIApp.register.exit.connect(self.generate_nginx_config)
        WSGIApp.activate.exit.connect(self.activate_nginx_config)


plugin = NginxPlugin
