import jinja2
from logbook import Logger
from pathlib import Path


def remove_suffix(suffix, s):
    if not suffix:
        return s

    if s.endswith(suffix):
        return s[:-len(suffix)]

    return s


class Plugin(object):
    def __init__(self, deploy, name=None):
        self.name = name or remove_suffix('plugin', self.__class__.__name__)
        self.log = Logger(self.__class__.__name__.lower())

        self.log.debug('{} initialized'.format(self.name))

        self.base_dir = Path(__file__).parent

        # initialize templates
        template_path = self.base_dir / 'templates'
        if template_path.exists():
            self.jinja_env = jinja2.Environment(
                loader=jinja2.PackageLoader(__name__)
            )

        # load possible default configuration
        defaults_file = self.base_dir / 'defaults.cfg'
        if defaults_file.exists():
            deploy.config.read_file(open(defaults_file))

        self.register(deploy)

    def register(self, deploy):
        pass

    def render_template(self, template_name, **kwargs):
        if not hasattr(self.jinja_env):
            return RuntimeError('Plugin {} has no template path'.format(
                self.__class__.__name__
            ))
        tpl = self.jinja_env.get_template(template_name)
        return tpl.render(**kwargs)

    def output_template(self, template_name, dest, **kwargs):
        with open(dest, 'w') as out:
            self.log.info('Writing {}'.format(dest))
            out.write(self.render_template(dest, **kwargs))
