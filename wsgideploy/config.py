from cmath import isinf
from copy import copy
import json
import os


class ConfigDict(object):
    def __init__(self, defaults={}):
        self._confs = [defaults]

    def copy(self):
        return copy(self)

    def __getitem__(self, name):
        for conf in self._confs:
            if name in conf:
                return conf[name]
        raise KeyError(name)

    def get(self, name, *args):
        try:
            return self[name]
        except KeyError:
            if args:
                return args[0]
            raise

    def get_path(self, base, *args):
        return os.path.abspath(
            os.path.join(os.path.expanduser(self[base]), *args)
        )

    def keys(self):
        ks = set()
        for conf in self._confs:
            ks.update(conf.keys())
        return ks

    def load_file(self, fp):
        data = json.load(fp)
        if not isinstance(data, dict):
            raise ValueError('Dictionary expected')
        self._confs.insert(0, data)

    def load_files(self, config_files):
        for name in config_files:
            path = os.path.expanduser(name)

            if not os.path.exists(path):
                continue

            try:
                with open(path) as fp:
                    self.load_file(fp)
            except Exception as e:
                raise ValueError('Could not parse configuration file {!r}: {}'
                                 .format(name, e))
