import application
import traceback
from page_log import NullLogger

class AmazingException(Exception):
    pass

class FakeAPI(object):
    def __init__(self, app):
        self.messages = []
        self.app = app

    def startup(self):
        self.messages.append(('startup', dict(self.app.status),
                              self.app.errors))
        return {}

    def message(self, messages, errors):
        self.messages.append(('report', dict(self.app.status), messages[:],
                              dict(errors)))
        return {}

    def record_pdd(self, message):
        pass


class FakePager(object):
    is_open = True

    def __init__(self, content):
        self.content = iter(content)

    def readline(self):
        for line in self.content:
            print line
            return line


def on_exception_main(exception):
    traceback.print_exc()


def create_pager(pages):
    pagerpi = application.PagerPI(pager=FakePager(pages),
                                  pagerrc=['tests', 'pagerrc.json'])
    pagerpi.ROLLOFF_SEC = [1.0]
    pagerpi.arena_api = FakeAPI(pagerpi)
    pagerpi.status_log = pagerpi.arena_api
    pagerpi.config['silent'] = True
    pagerpi.pushover = application.SilentPushover()
    pagerpi.on_exception_main = on_exception_main
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
    message = report[2][0]
    assert message['message'] == "Yes"
    assert message['type'] == "pager_message"
    assert 'ts' in message

def assert_reconnect_succeeded(messages, xmessages, xerrors_success=()):
    """Assert that one report fails, then the application reconnects and
    successfully reports.

    """
    assert len(messages) == 4, '\n'.join("%60r" % (x,) for x in messages)
    _, report_fail, _, errors_fail = messages[1]
    _, report_recon, _ = messages[2]
    _, report_success, messages_success, errors_success = messages[3]

    assert report_fail['last_read_time'] is not None
    assert report_success['last_read_time'] is not None
    assert report_fail['last_read_time'] < report_success['last_read_time']
    assert report_recon['last_read_time'] == report_fail['last_read_time']
    assert set(errors_success) == set(xerrors_success)
    assert len(messages_success) == len(xmessages)
    for msg, xmsg in zip(messages_success, xmessages):
        assert msg['message'] == xmsg

def test_reconnect_on_report_exception():
    """If an exception occurs when contacting message service

    The application should reconnect and send the pending message
    """
    class FailAPI(FakeAPI):
        report_fail = True
        def message(self, messages, errors):
            super(FailAPI, self).message(messages, errors)
            if self.report_fail:
                self.report_fail = False
                raise AmazingException("No dice.")
            else:
                self.app.stop = True
                return {'errors' : []}

    xmessages = ["No.", "Yes."]
    pagerpi = create_pager(xmessages)
    pagerpi.arena_api = FailAPI(pagerpi)
    pagerpi.status_log = pagerpi.arena_api

    pagerpi.main()

    assert_reconnect_succeeded(pagerpi.arena_api.messages, ["No", "Yes"],
                               ["AmazingException: No dice.\n"])

def test_reconnect_on_report_failure():
    """If an error occurs when saving messages

    The application should reconnect and send the pending message
    """
    class FailAPI(FakeAPI):
        report_fail = True
        def message(self, messages, errors):
            super(FailAPI, self).message(messages, errors)
            if self.report_fail:
                self.report_fail = False
                return {'errors' : 'AmazingException: No dice'}
            else:
                self.app.stop = True
                return {'errors' : []}

    xmessages = ["No.", "Yes."]
    pagerpi = create_pager(xmessages)
    pagerpi.arena_api = FailAPI(pagerpi)
    pagerpi.status_log = pagerpi.arena_api

    pagerpi.main()

    assert_reconnect_succeeded(pagerpi.arena_api.messages, ["No", "Yes"])
