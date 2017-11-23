from __future__ import print_function

import config_stuff
import serial
import signal
import requests
import time
import traceback
import read_page
import random
import urllib

from subprocess import check_output
from datetime import datetime
from page_log import Logger, NullLogger
from status_api import StatusLog
from actions import perform


class SilentPushover(object):
    def send_message(self, *args, **kwargs):
        pass

class PagerPI(object):
    debug = False
    verbose = False
    stop = False
    startup_attempt = 0
    needs_startup = True
    start_sleep_intervals = [5, 15, 30, 60, 120, 240]
    need_sleep = None
    ip_addresses = "UNSET"

    def __init__(self, pager=None, port='/dev/serial0', baud=9600,
                 timeout=5.*60, override_config=None, pagerrc=None):
        # A list of pager messages that we have received but not
        # logged to the status server.
        self.messages = []

        # A map from traceback to a list of timestamps of when the
        # errors occurred that have not yet been sent to the status
        # server.
        self.errors = {}

        if pagerrc is None:
            pagerrc = ['..', 'pagerrc.json']

        # load configuration data.
        self.config = config_stuff.configure(pagerrc, override_config or {})

        # Actions requested by the server, yet to be performed.
        self.actions = []
        self.perform = perform

        # The serial device that we are reading pager messages from.
        self.pager = pager
        if pager is None:
            self.pager = serial.Serial(port=port, baudrate=baud,
                                       timeout=timeout)

        # An object that sends messages to the status service.
        self.status_log = StatusLog(self)

        # Application metrics.
        self.status = {'alert_messages': 0,
                       'other_messages': 0,
                       'last_read_time': None}

        # An object that can send messages via pushover.
        try:
            import pushover
            self.pushover = pushover.Client()
            self.public_pushover = pushover.Client(profile="Public")
        except Exception:
            self.pushover = SilentPushover()
            self.public_pushover = self.pushover

    @property
    def log(self):
        if self.config.get('silent'):
            return NullLogger()
        return Logger(self.verbose, self.config.get('lineFile'))

    def startup(self):
        """Perform startup tasks
        """
        try:
            # report our IP address via pushover.
            self.send_addresses()

            # report to the status server that we have started.
            self.status_log.startup()
        except Exception as e:
            self.on_exception(e)

            # don't try to start up again for this many seconds.
            sleep_intervals = self.start_sleep_intervals
            if self.startup_attempt < len(sleep_intervals):
                self.need_sleep = sleep_intervals[self.startup_attempt]
                self.startup_attempt += 1
            else:
                self.need_sleep = sleep_intervals[-1]
            raise
        else:
            self.startup_attempt = 0
            self.needs_startup = False

    def main_once(self):
        # Perform any pending requested actions.
        while self.actions:
            self.perform(self, self.actions.pop(0))

        if self.needs_startup:
            # Connect to the server to report our version and state.
            self.startup()

        # Open the serial port.
        if not self.pager.is_open:
            try:
                pager.open()
            except Exception as e:
                self.need_sleep = 5
                raise Exception("Failed to open serial port: %s" %
                                (e.message,))

        # read one line from the pager receiver
        try:
            data = self.pager.readline()
        except Exception as e:
            self.pager.close()
            raise

        if data:
            self.status['last_read_time'] = datetime.now()
            self.log.pager_log_all(data)
            # parse & handle the data that we read.  this will create
            # a pdd request in Arena if the message is an alert.
            self.handle_serial_data(data)
        elif self.verbose:
            print('No data within timeout period')

        # notify the status server of our activity.
        try:
            self.status_log.message(self.messages, self.errors)
        except Exception as exception:
            self.on_exception(exception)
        else:
            self.messages = []
            self.errors = {}

    def main(self):
        while not self.stop:
            try:
                self.main_once()
            except Exception as exception:
                self.on_exception(exception)
            if self.need_sleep is not None:
                time.sleep(self.need_sleep)
                self.need_sleep = None

    def shutdown_handler(self, signum, frame):
        print("Received shutdown signal")
        raise _SHUTDOWN

    def send_addresses(self):
        ip_addresses = check_output(["hostname", "-I"]).strip()
        if ip_addresses != self.ip_addresses:
            print("Sending IP Addresses [", ip_addresses, "]")
            self.pushover.send_message(ip_addresses, title="My IP")
            self.ip_addresses = ip_addresses

    def handle_serial_data(self, pager_message):
        alert = read_page.read_alert_message(self, pager_message)
        if alert:
            if self.debug and alert['lat'] is None:
                self.make_random_geo(alert)
            if self.verbose:
                read_page.show_alert_message(alert)
            else:
                print('alert message: %r' % (alert['message'],))
            self.on_alert_message(alert)
        else:
            self.on_unhandled_message(pager_message)
            print('other message: %r' % (pager_message,))

    def make_random_geo(self, alert):
        """For debugging the Arena integration.

        Generate a random location and whether it is an aircraft message.
        """
        if app.verbose:
            print("NO Geo Coords - going random!")
        alert['latitude'] = -37.616+random.uniform(-1, 1)
        alert['longitude'] = 144.420+random.uniform(-1, 1)
        if random.randint(0,9) > 5:
            if app.verbose:
                print("Random aircraft message generated!")
            alert['aircraftMsg'] = 1

    def send_public_message(self, alert):
        self.public_pushover.send_message(alert['message'],
                                          title="CFA Alert")

    def on_alert_message(self, alert):
        self.messages.append({'ts' : str(datetime.now()),
                              'type' : 'alert',
                              'message' : alert['message']})
        self.send_public_message(alert)
        headers = {"x-version": self.config['xver'],
                   "authorization": self.config['auth'],
                   "content-type": "application/x-www-form-urlencoded"}
        if alert['lat'] is not None:
            response = requests.post(self.config['pddUrl'],
                                     headers=headers,
                                     data=urllib.urlencode(alert))
            response.raise_for_status()
        self.status['alert_messages'] += 1

    def on_unhandled_message(self, message):
        self.messages.append({'ts' : str(datetime.now()),
                              'type' : 'pager_message',
                              'message' : read_page.clean_message(message)})
        self.status['other_messages'] += 1

    def on_exception(self, exception):
        exception_text = traceback.format_exception_only(type(exception),
                                                         exception)
        now = datetime.now()
        self.errors.setdefault(''.join(exception_text), []).append(
            {'ts' : str(now)})
        self.log.report_exception(now, exception)


class _Shutdown(BaseException):
    """A request for shutdown of the pager service.

    Note that this is a BaseException, which means it will not be
    caught by the usual exception machinery.
    """

_SHUTDOWN = _Shutdown("TERM signal received")


def main(debug=False, verbose=True, no_pushover=False):
    print("PagerPI Start")
    if verbose:
        print(datetime.now().isoformat())
    try:
        pagerpi = PagerPI()
        pagerpi.debug = debug
        pagerpi.verbose = verbose
        if no_pushover:
            pagerpi.send_addresses = lambda: None
        signal.signal(signal.SIGTERM, pagerpi.shutdown_handler)
        pagerpi.main()
    except (_Shutdown, KeyboardInterrupt):
        if debug:
            import traceback
            traceback.print_exc()
        pass


if __name__ == '__main__':
    main()
