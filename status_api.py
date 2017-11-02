import requests
import json

_SENTINEL = object()


class StatusLog(object):
    """Interface to the pager status service.

    The pager should periodically report via the message() method.
    This lets the administrators know that the pager is up and
    running, and what sort of messages it is receiving.

    """

    def __init__(self, app):
        self.app = app

    def config(self, key, default=_SENTINEL):
        if default is _SENTINEL:
            return self.app.config[key]
        return self.app.config.get(key, default)

    def request(self, page, data):
        res = requests.post(self.app.config['pager_log_host'] + page,
                            data=data)
        res.raise_for_status()
        data = res.json()
        if 'commands' in data:
            self.app.actions.extend(data['commands'])
        return data

    def startup(self):
        """Report startup information to the status service
        """
        res = self.request('pager/startup', data ={
            'ip_address' : self.config('ip_address', '?'),
            'revision' : self.config('revision', '?'),
            'token' : self.config('token'),
            'hostname' : self.config('hostname', '?'),
        })
        self.status_key = res['key']
        return res

    def message(self, messages, errors):
        """Report messages and errors to the status service"""
        return self.request('pager/message2', data={
            'token' : self.config('token'),
            'status_key' : self.status_key,
            'messages' : json.dumps(messages),
            'errors' : json.dumps(errors),
            'report' : self.app.status,
            'hostname' : self.config('hostname', '?'),
        })
