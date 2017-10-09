import application
from page_log import NullLogger

class AmazingException(Exception):
    pass

class FakeAPI(object):
    def __init__(self):
        self.messages = []

    def startup(self, app):
        self.messages.append(('startup', dict(app.status)))
        app.errors = {}

    def report(self, app):
        self.messages.append(('report', dict(app.status)))
        app.errors = {}

    def log_message(self, app, message):
        pass


class FakePager(object):
    is_open = True

    def __init__(self, content):
        self.content = iter(content)

    def readline(self):
        for line in self.content:
            return line


def create_pager(pages):
    pagerpi = application.PagerPI(pager=FakePager(pages))
    pagerpi.pagerrc = ['tests', 'pagerrc.json']
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
        'startup', {'errors': [], 'alert_messages': 0, 'other_messages': 0,
                    'last_read_time' : None})
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

    startup, (_, report_fail), recon, (_, report_success) = (
        pagerpi.arena_api.messages)

    print pagerpi.arena_api.messages

    assert report_fail['last_read_time'] is not None
    assert report_success['last_read_time'] is not None
    assert report_fail['last_read_time'] < report_success['last_read_time']
    assert recon[1]['last_read_time'] == report_fail['last_read_time']
    assert len(recon[1]['errors']) == 1
    assert recon[1]['errors'][0]['message'] == ['AmazingException: No dice.\n']
    assert not report_success['errors']

