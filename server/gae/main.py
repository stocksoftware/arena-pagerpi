import webapp2
import json
import logging
import traceback
import os # update
from datetime import datetime, timedelta
from google.appengine.ext.ndb import Key

from pager.helpers import is_equal, parse_dt, JINJA
from pager.model import Report, Status, PagerException, Message
from pager.over import send_messages

capability = ''

status_cap = ''

EXCEPTION_MAX = 20
MESSAGE_MAX = 20
REPORT_MAX = 5

class AuthorisationError(Exception):
    pass


def get_status_json(request, result):
    try:
        return get_status_r(request)
    except AuthorisationError as ae:
        result.setdefault('errors', []).append(ae.message)
    return None, None


def get_status_r(request):
    return get_status(request.get('token'), request.remote_addr,
                      request.get('status_key'), request.get('hostname'))


def get_status(token, remote_addr, status_key=None, hostname=None):
    if not token or not is_equal(token, capability):
        raise AuthorisationError("Please supply a valid service capability")

    if status_key:
        pager_key = Key(urlsafe=status_key)
        if not is_equal(pager_key.kind(), 'Status'):
            raise AuthorisationError("Key provided is not to a Status")
    else:
        if not hostname:
            raise AuthorisationError("Cannot determine pager-id from request")
        status_id = "%s_%s" % (hostname, remote_addr)
        pager_key = Key(Status, capability, Status, status_id)

    pager_ob = pager_key.get()
    if pager_ob and not is_equal(pager_ob.public_ip, remote_addr):
        result['errors'].append('Please start-up on IP change')
        return

    return pager_key, pager_ob


class ReportPage(webapp2.RequestHandler):
    def get(self):
        pass

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        result = {'request' : 'report'}
        key, status = get_status_json(self.request, result)
        if key is None:
            self.response.write(json.dumps(result, indent=2))
            return

        report = Report(parent=key)
        report.populate(
            public_ip=self.request.remote_addr,
            last_read_time=parse_dt(self.request.get('last_read_time')),
            alert_messages=int(self.request.get('alert_messages')),
            other_messages=int(self.request.get('other_messages'))
        )
        result['report_id'] = report.put().urlsafe()
        self.response.write(json.dumps(result, indent=2))


class UpdatePage(webapp2.RequestHandler):
    def get(self):
        self.post()
    def post(self):
        token = self.request.get('token')
        if not token or not is_equal(token, capability):
            raise AuthorisationError("Please supply a valid service capability")

        with open(os.path.join(os.path.dirname(__file__), 'update.py')) as f:
            script = f.read()
        self.response.headers['Content-Type'] = 'application/json'
        result = {
            'script_id' : 'experimental-0.0-47-gee04f8c',
            'script' : script,
        }
        self.response.write(json.dumps(result, indent=2))

def load_status_data2(status):
    existing_messages = Message.query(
        ancestor=status.key).order(-Message.report_time).fetch(limit=50)

    messages = [{'ts' : message.report_time,
                 'message' : message.message}
                for message in reversed(existing_messages)
                if message.report_time is not None]

    return {
        'hostname' : (status.hostname or '').strip() or '<unnamed>',
        'public_ip' : status.public_ip,
        'private_ip' : status.private_ip,
        'revision' : status.revision,
        'report_time' : status.report_time,
        'messages' : messages,
    }


class StartupPage(webapp2.RequestHandler):
    def get(self):
        token = self.request.get('token')
        if not token:
            return
#        if not is_equal(token, capability):
#            return
        parent = Key(Status, capability)
        statuses = Status.query(ancestor=parent)

        pagers = [load_status_data2(status) for status in statuses]
        
        if self.request.get('json'):
            result = {'pagers' : pagers}
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(result, indent=2,
                                           default=lambda x: str(x)))
        else:
            pagers = [load_status_data2(status) for status in statuses]
            template = JINJA.get_template('status.html')
            self.response.write(template.render({
                'pagers' : pagers,
            }))

    def post(self):
        hostname = self.request.get('hostname') or ''
        public_ip = self.request.remote_addr
        key, status = get_status(self.request.get('token'),
                                 public_ip, hostname=hostname)

        status_id = "%s_%s" % (hostname, public_ip)
        parent = Key(Status, capability)
        key = Key('Status', status_id, parent=parent)
        status = key.get()

        if not status:
            status = Status(id=status_id, parent=parent)

        status.populate(public_ip =public_ip,
                        report_time = datetime.now(),
                        private_ip = self.request.get('ip_address'),
                        revision = self.request.get('revision'),
                        hostname = hostname)

        key = status.put()
        result = {'request' : 'startup', 'key' : key.urlsafe()}
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(result, indent=2))

        try:
            self.status_cleanup()
        except Exception:
            pass

    def status_cleanup(self):
        old_stati = Status.query(
            Status.report_time < (datetime.now() - timedelta(1, 0, 0)))
        for status in old_stati.iter(keys_only=True):
            status.delete()


class StatusPage(webapp2.RequestHandler):
    def get(self):
        pass


class ReportPage2(webapp2.RequestHandler):
    def post(self):
        result = {'request' : 'message2',
                  'errors' : [],
                  'info' : [],
                  'commands' : []}
        self.response.headers['Content-Type'] = 'application/json'
        self.inner_post(result)
        self.response.write(json.dumps(result, indent=2))

    def inner_post(self, result):
        pager, status = get_status_json(self.request, result)
        if status is None:
            if pager is not None:
                result['errors'].append("Needs start-up")
            return

        now = datetime.now()
        status.populate(report_time=now)
        status.put()

        try:
            report = self.request.get('report')
            if report:
                self.save_report(pager, json.loads(report), now)
        except Exception as e:
            logging.exception(e.message)
            result['errors'].append('Unable to save report: %s' % (
                ''.join(traceback.format_exception_only(type(e), e)),))

        try:
            errors = self.request.get('errors')
            if errors:
                self.save_errors(result, pager, json.loads(errors))
        except Exception as e:
            logging.exception(e.message)
            result['errors'].append('Unable to save errors: %s' % (
                ''.join(traceback.format_exception_only(type(e), e)),))

        try:
            messages = self.request.get('messages')
            if messages:
                self.save_messages(result, pager, json.loads(messages))
        except Exception as e:
            logging.exception(e.message)
            result['errors'].append('Unable to save messages: %s' % (
                ''.join(traceback.format_exception_only(type(e), e)),))

    def save_report(self, key, report_json, now):
        reports = Report.query(ancestor=key).order(
            Report.report_time).fetch(REPORT_MAX * 2)

        if len(reports) > REPORT_MAX * 1.5:
            for report in reports[:REPORT_MAX]:
                report.key.delete()

        last_read_time = datetime.strptime(report_json.get('last_read_time', None),
                                           "%Y-%m-%d %H:%M:%S.%f")
        alert_messages = report_json.get('alert_messages', None)
        other_messages = report_json.get('other_messages', None)
        Report(parent=key,
               report_time=now,
               last_read_time=last_read_time,
               alert_messages=alert_messages,
               other_messages=other_messages).put()

    def save_errors(self, result, key, error_json):
        new_errors = [
            (parse_dt(t.get('ts')), traceback)
            for traceback, times in error_json.items() for t in times]
        new_errors.sort()
        errors = PagerException.query(ancestor=key).order(
            PagerException.report_time).fetch(EXCEPTION_MAX * 2)

        let_remain = max(0, EXCEPTION_MAX - len(new_errors))
        to_delete = max(0, len(errors) - let_remain)
        for error in errors[:to_delete]:
            error.key.delete()

        to_save = new_errors[-EXCEPTION_MAX:]

        for dt, tb in to_save:
            if dt and tb:
                PagerException(parent=key, traceback=tb, report_time=dt).put()
        result['info'].append("%s errors saved" % (len(to_save),))

    def save_messages(self, result, key, message_json):
        #logging.info(json.dumps(message_json, indent=2))
        new_messages = message_json
        errors = Message.query(ancestor=key).order(
            Message.report_time).fetch(MESSAGE_MAX * 2)

        let_remain = max(0, MESSAGE_MAX - len(new_messages))
        to_delete = max(0, len(errors) - let_remain)
        for error in errors[:to_delete]:
            error.key.delete()

        to_save = new_messages[-MESSAGE_MAX:]
        for entry in to_save:
            message = entry['message']
            timestamp = parse_dt(entry['ts'])
            if message and timestamp:
                Message(parent=key, message=message,
                        report_time=timestamp).put()
        result['info'].append("%s messages saved" % (len(to_save),))

        for entry in new_messages:
            if entry.get('aircraftMsg', False):
                send_messages(entry)


APP = webapp2.WSGIApplication([
    webapp2.Route('/pager/report', ReportPage, 'report'),
    webapp2.Route('/pager/startup', StartupPage, 'startup'),
#    webapp2.Route('/pager/status', StatusPage, 'status'),
    webapp2.Route('/pager/message2', ReportPage2, 'message2'),
    webapp2.Route('/pager/update', UpdatePage, 'update'),
])
