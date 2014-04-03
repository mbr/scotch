import json
import os

from werkzeug.datastructures import MultiDict


def load_config(config_files, defaults=None):
    cfg = MultiDict(defaults)

    for path in config_files:
        try:
            if not os.path.exists(path):
                continue

            with open(os.path.expanduser(path)) as fp:
                data = json.load(fp)
            cfg.update(data)
        except Exception as e:
            raise ValueError('Could not parse configuration file {!r}: {}'
                             .format(path, e))

    return cfg
