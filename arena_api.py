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
            auth = self.app.config.get('keycloak', False)
            if not auth:
                return 'test'
            result = requests.post(auth['url'], data={
                'client_id': auth['client_id'],
                'client_secret': auth['client_secret'],
                'grant_type': auth['grant_type'],
                'username': auth['username'],
                'password': auth['password']
            })
            print result.text
            result.raise_for_status()
            self._authorisation = result.json()['access_token']
        return self._authorisation

    def record_pdd(self, alert):
        may_retry_auth = False
        while True: # Retry if it fails to auth
            authorisation = self.authorisation()
            try:
                self._pdd(alert, authorisation)
                return
            except requests.HTTPError as error:
                if error.response.status_code == 403 and may_retry_auth:
                    self._authorisation = None
                    may_retry_auth = False
                else:
                    raise

    def _pdd(self, alert, authorisation):
        pdd_config = self.app.config['pdd']
        headers = {"x-version": pdd_config['xver'],
                   "authorization": authorisation,
                   "content-type": "application/x-www-form-urlencoded"}
        response = requests.post(pdd_config['url'],
                                 headers=headers,
                                 data=urllib.urlencode(alert))
        response.raise_for_status()
