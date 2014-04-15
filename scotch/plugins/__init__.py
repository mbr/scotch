import inspect
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
    def __init__(self, site, name=None):
        self.name = name or remove_suffix('plugin', self.__class__.__name__)
        self.log = Logger(self.__class__.__name__.lower())

        self.log.debug('{} initialized'.format(self.name))
        self.base_dir = Path(inspect.getfile(self.__class__)).parent

        # initialize templates
        template_path = self.base_dir / 'templates'
        if template_path.exists():
            self.jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(template_path))
            )

        # load possible default configuration
        self.register(site)

    @property
    def DEFAULTS_FILE(self):
        return self.base_dir / 'defaults.cfg'

    def register(self, site):
        pass

    def enable_app(self, app):
        pass

    def render_template(self, template_name, **kwargs):
        if not hasattr(self, 'jinja_env'):
            return RuntimeError('Plugin {} has no template path'.format(
                self.__class__.__name__
            ))
        tpl = self.jinja_env.get_template(template_name)
        return tpl.render(**kwargs)

    def output_template(self, template_name, dest, **kwargs):
        if not dest.parent.exists():
            self.log.warning('Path {} did not exist and was created'.format(
                             dest.parent,
            ))
            dest.parent.mkdir(parents=True)

        with dest.open('w') as out:
            self.log.info('Writing {}'.format(dest.resolve()))
            out.write(self.render_template(template_name, **kwargs))
