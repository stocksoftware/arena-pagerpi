"""Functions to manage runtime configuration of the pager service.
"""

from __future__ import print_function
import requests
import json
import os
import os.path

from subprocess import check_output, CalledProcessError
from datetime import datetime

REPO = os.path.abspath(os.path.dirname(__file__))

def form(d):
    return {'content' : json.dumps(d),
            'token' : d['token']}


def configure(app):
    with open(os.path.join(REPO, *app.pagerrc)) as f:
        app.config = json.load(f)

    try:
        app.config['revision'] = check_output(["git", "describe", "--tags"],
                                              cwd=REPO)
    except CalledProcessError:
        pass

    try:
        app.config['ip_address'] = check_output(["hostname", "-I"])
    except CalledProcessError:
        pass

    try:
        app.config['hostname'] = check_output(["hostname", "-f"])
    except CalledProcessError:
        pass


def startup(app):
    """Report startup information to Arena and get configuration data.
    """
    try:
        configure(app)
        report_url = app.config.get('reportUrl', '')
        if report_url:
            res = requests.post(report_url + "/startup", data={
                'token' : app.config['token'],
                'ip_address' : app.config.get('ip_address', '?'),
                'revision' : app.config.get('revision', '?'),
                'hostname' : app.config.get('hostname', '?'),
            })
            res.raise_for_status()
            app.config['status_key'] = res.json()['key']
    except Exception as e:
        app.on_exception(e)
        raise


def report(app):
    data = dict(app.status)
    data['token'] = app.config['token']
    data['status_key'] = app.config['status_key']
    last_read_time = data['last_read_time']
    if last_read_time is not None:
        data['last_read_time'] = str(last_read_time)
    now = data['report_time'] = str(datetime.now())
    try:
        report_url = app.config.get('reportUrl', None)
        if report_url:
            res = requests.post(report_url + "/report", data=data)
            res.raise_for_status()
    except (OSError, requests.exceptions.HTTPError) as e:
        app.on_exception(e)
    else:
        app.status['last_report'] = now
        perform(res)


def log_messages(app, messages):
    now = str(datetime.now())
    data = {
        'token': app.config['token'],
        'hostname': app.config['hostname'],
        'status_key': app.config['status_key'],
        'messages': json.dumps(messages),
        'errors': json.dumps(app.errors),
    }
    try:
        report_url = app.config.get('reportUrl', None)
        if report_url:
            res = requests.post(report_url + "/message2", data=data)
            res.raise_for_status()
    except (OSError, requests.exceptions.HTTPError) as e:
        app.on_exception(e)
    else:
        app.errors = {}
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

