from contextlib import contextmanager
import inspect
import os
import jinja2
from logbook import Logger
from pathlib import Path


def remove_suffix(suffix, s):
    if not suffix:
        return s

    if s.endswith(suffix):
        return s[:-len(suffix)]

    return s


@contextmanager
def new_file(path, perm=0644, base=0666, mode='w'):
    old_umask = os.umask(base ^ perm)
    with open(str(path), mode) as f:
        yield f
    os.umask(old_umask)


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
                loader=jinja2.FileSystemLoader(str(template_path)),
                extensions=['jinja2.ext.with_']
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

    def output_template(self, template_name, dest, _mode=0o644, **kwargs):
        if not dest.parent.exists():
            self.log.warning('Path {} did not exist and was created'.format(
                             dest.parent,
            ))
            dest.parent.mkdir(parents=True)

        with new_file(dest, _mode) as out:
            self.log.info('Writing {}'.format(dest.resolve()))
            out.write(self.render_template(template_name, **kwargs))
