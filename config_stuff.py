"""Functions to manage runtime configuration of the pager service.
"""

from __future__ import print_function
import requests
import traceback
import json
import os
import sys

from subprocess import check_output, CalledProcessError
from datetime import datetime

CONFIG = {}
STATUS = {'errors': [],
          'alert_messages': 0,
          'other_messages': 0}

FAIL_LOG = 'fail.log'


def fail_and_exit(text):
    """Log failure for next time we start, and exit the program.
    """
    with open(FAIL_LOG, 'a') as f:
        f.write("%s\n" % datetime.now())
        f.write(text)
        f.write("\n")
    sys.exit(text)


try:
    REMOTE = os.environ['ARENA_REMOTE'].rstrip('/')
except KeyError:
    fail_and_exit("Please set the environment variable ARENA_REMOTE to "
                  "a pager endpoint.\n"
                  "e.g. http://arenatest.nafc.org.au/register/api/pddPager\n"
                  "or http://10.0.0.130:8880")

if '://' not in REMOTE:
    fail_and_exit("Invalid ARENA_REMOTE: missing protocol (eg http://)")


def form(d):
    return {'content' : json.dumps(d)}


def startup():
    """Report startup information to Arena and get configuration data.
    """
    try:
        revision = check_output(["git", "describe", "--tags"])
    except CalledProcessError:
        revision = ""

    try:
        ip_address = check_output(["hostname", "-I"]).split()

        config = requests.post(REMOTE + "/startup",
                               data={'revision': revision,
                                     'ip-address': ':'.join(ip_address)})
        data = config.json()
        CONFIG.clear()
        CONFIG.update(data)
    except Exception as e:
        with open(FAIL_LOG, 'a') as f:
            f.write("%s\n" % datetime.now())
            traceback.print_exc(file=f)
            f.write("\n")
        raise


def report():
    data = {}
    data.update(STATUS)
    now = data['report_time'] = str(datetime.now())
    try:
        res = requests.post(REMOTE + "/report", data=form(data))
        res.raise_for_status()
    except (OSError, requests.exceptions.HTTPError) as e:
        STATUS['errors'].append(e.message)
    else:
        STATUS['errors'] = []
        STATUS['last_report'] = now
        perform(res)

ACTIONS = {}

def action(f):
    ACTIONS[f.__name__] = f
    return f


def perform(data):
    """Do things that the server has requested.

    Right now, no actions are defined.  We can add actions here.
    """
    try:
        data = data.json()
        #except simplejson.
    except Exception:
        return
    for command in data.get('commands', ()):
        name, args = command
        action = ACTIONS.get(name, default_action(name))
        action(*args)


def default_action(name):
    def action(*args):
        print("no such action %s (%d pos args)" % (name, len(args)))
    return action


@action
def clear_error():
    os.remove(FAIL_LOG)


if __name__ == '__main__':
    STATUS['nteeth'] = 25
    report()
