"""Functions to manage runtime configuration of the pager service.
"""

from __future__ import print_function
import requests
import traceback
import json
import os
import sys
import os.path

from subprocess import check_output, CalledProcessError
from datetime import datetime

REPO = os.path.abspath(os.path.dirname(__file__))
FAIL_LOG = os.path.join(os.path.dirname(REPO), 'fail.log')

def fail_and_exit(text):
    """Log failure for next time we start, and exit the program.
    """
    with open(FAIL_LOG, 'a') as f:
        f.write("%s\n" % datetime.now())
        f.write(text)
        f.write("\n")
    sys.exit(text)


def form(d):
    return {'content' : json.dumps(d)}


def configure(app):
    with open(os.path.join(REPO, *app.pagerrc)) as f:
        app.config = json.load(f)

    try:
        app.config['revision'] = check_output(["git", "describe", "--tags"],
                                              cwd=REPO)
    except CalledProcessError:
        app.config['revision'] = 'Unknown'

    try:
        app.config['ip_address'] = check_output(["hostname", "-I"]).split()
    except CalledProcessError:
        app.config['ip_address'] = ['not connected?']


def startup(app):
    """Report startup information to Arena and get configuration data.
    """
    try:
        configure(app)
        report_url = app.config.get('reportUrl', '')
        if report_url:
            requests.post(report_url + "/startup", data=form(app.config))
    except Exception as e:
        with open(FAIL_LOG, 'a') as f:
            f.write("%s\n" % datetime.now())
            traceback.print_exc(file=f)
            f.write("\n")
        raise


def report(app):
    data = dict(app.status)
    now = data['report_time'] = str(datetime.now())
    try:
        report_url = app.config.get('reportUrl', None)
        if report_url:
            res = requests.post(report_url + "/report", data=form(data))
        res.raise_for_status()
    except (OSError, requests.exceptions.HTTPError) as e:
        app.status['errors'].append(e.message)
    else:
        app.status['errors'] = []
        app.status['last_report'] = now
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
