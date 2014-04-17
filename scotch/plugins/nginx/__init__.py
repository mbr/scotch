from pathlib import Path
import subprocess
from scotch.app import WSGIApp
from scotch.plugins import Plugin


class NginxPlugin(Plugin):
    def activate_nginx_config(self, app):
        """Generates the necessary nginx site configuration for the app."""
        conf_mode = int(app.config['nginx']['config_mode'], 8)

        # first, generate all domains/sites
        for domain in app.domains:
            # replace wildcards
            safe_name = domain.replace('*', '_')

            # generate the domain configuration
            output_fn = (Path(app.config['nginx']['sites_path'])
                         / 'scotch_domain_{}'.format(safe_name))

            domain_path = (Path(app.config['nginx']['domains_path']) /
                           '{}'.format(safe_name))
            include_path = str(domain_path) + '/*'

            self.output_template('domain.conf', output_fn, config=app.config,
                                 domain=domain, safe_name=safe_name,
                                 include_path=include_path,
                                 _mode=conf_mode)

            # for every domain, generate the site configuration
            output_fn = domain_path / app.name
            self.output_template('app.conf', output_fn, config=app.config,
                                 _mode=conf_mode)

        subprocess.check_call([app.config['nginx']['reload_command']],
                              shell=True)

    def enable_app(self, app):
        WSGIApp.activate.exit.connect(self.activate_nginx_config)


plugin = NginxPlugin
