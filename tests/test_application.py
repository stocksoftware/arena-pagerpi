import application
from page_log import NullLogger

class AmazingException(Exception):
    pass

class FakeAPI(object):
    def __init__(self):
        self.messages = []

    def startup(self, app):
        self.messages.append(('startup', dict(app.status), app.errors))
        app.errors = {}

    def report(self, app):
        self.messages.append(('report', dict(app.status), app.errors))
        app.errors = {}

    def log_messages(self, app, message):
        pass


class FakePager(object):
    is_open = True

    def __init__(self, content):
        self.content = iter(content)

    def readline(self):
        for line in self.content:
            return line


def create_pager(pages):
    pagerpi = application.PagerPI(pager=FakePager(pages),
                                  pagerrc=['tests', 'pagerrc.json'])
    pagerpi.arena_api = FakeAPI()
    pagerpi.config['silent'] = True
    pagerpi.pushover = application.SilentPushover()
    return pagerpi

def test_normal_interaction():
    pagerpi = create_pager(["Yes"])
    pagerpi.main_once()
    assert len(pagerpi.arena_api.messages) == 2
    startup, report = pagerpi.arena_api.messages
    assert startup == (
        'startup', {'alert_messages': 0, 'other_messages': 0,
                    'last_read_time' : None}, {})
    assert report[0] == 'report'
    assert 'last_read_time' in report[1]
    assert report[1]['other_messages'] == 1

def test_reconnect_on_report_failure():
    class FailAPI(FakeAPI):
        report_fail = True
        def report(self, app):
            super(FailAPI, self).report(app)
            if self.report_fail:
                self.report_fail = False
                raise AmazingException("No dice.")
            else:
                app.stop = True

    pagerpi = create_pager(["No.", "Yes."])
    pagerpi.arena_api = FailAPI()
    # try:
    #     pagerpi.main_once()
    # except Exception:
    #     pass
    # else:
    #     assert False, "Did not attempt to report?"

    # pagerpi.main_once()
    pagerpi.main()
    
    assert len(pagerpi.arena_api.messages) == 4
    _, report_fail, errors_fail = pagerpi.arena_api.messages[1]
    _, report_recon, errors_recon = pagerpi.arena_api.messages[2]
    _, report_success, errors_success = pagerpi.arena_api.messages[3]

    print pagerpi.arena_api.messages

    assert report_fail['last_read_time'] is not None
    assert report_success['last_read_time'] is not None
    assert report_fail['last_read_time'] < report_success['last_read_time']
    assert report_recon['last_read_time'] == report_fail['last_read_time']
    assert len(errors_recon) == 1
    assert 'AmazingException: No dice.\n' in errors_recon
    assert not errors_success

