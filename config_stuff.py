"""Functions to manage runtime configuration of the pager service.
"""

from __future__ import print_function
import json

from os.path import abspath, join, dirname
from subprocess import Popen, PIPE

REPO = abspath(dirname(__file__))


def configure(app):
    with open(join(REPO, *app.pagerrc)) as f:
        config = json.load(f)

    def _set_from_application(field, cmd, **kwargs):
        config[field] = Popen(cmd, stdout=PIPE, cwd=REPO).communicate()[0]

    _set_from_application('revision', ["git", "describe", "--tags"])
    _set_from_application('ip_address', ["hostname", "-I"])
    _set_from_application('hostname', ["hostname", "-f"])

    config.update(app.default_config)
    return config
