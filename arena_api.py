import requests
import urllib

class ArenaAPI(object):
    def __init__(self, app):
        self.app = app
        self._authorisation = None

    def config(self, key):
        return self.app.config['arena'][key]

    def authorisation(self):
        if self._authorisation is None:
            result = requests.post(auth['url'], data={
                'client_id': auth['client_id'],
                'client_secret': auth['client_secret'],
                'grant_type': auth['grant_type'],
                'username': auth['username'],
                'password': auth['password']
            })
            result.raise_for_status()
            self._authorisation = result.json()['access_token']
        return self._authorisation

    def record_pdd(self, message):
        may_retry_auth = False
        while True: # Retry if it fails to auth
            authorisation = self.authorisation()
            try:
                self._pdd(message, authorisation)
                return
            except requests.HTTPError as error:
                if error.response.status_code == 403 and may_retry_auth:
                    self._authorisation = None
                    may_retry_auth = False
                else:
                    raise

    def _pdd(self, message, authorisation):
        headers = {"x-version": self.config('xver'),
                   "authorization": authorisation,
                   "content-type": "application/x-www-form-urlencoded"}
        response = requests.post(self.config['pddUrl'],
                                 headers=headers,
                                 data=urllib.urlencode(alert))
        response.raise_for_status()
