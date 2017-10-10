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


class SilentPushover(object):
    def send_message(self, *args, **kwargs):
        pass

class PagerPI(object):
    debug = False
    verbose = False
    stop = False
    start_sleep_idx = 0
    needs_startup = True
    start_sleep_intervals = [5, 15, 30, 60, 120, 240]
    need_sleep = None
    ip_addresses = "UNSET"
    pagerrc = ['..', 'pagerrc.json']

    def __init__(self, pager=None, port='/dev/serial0', baud=9600,
                 timeout=5.*60):
        self.messages = []
        self.errors = {}
        self.config = {}
        self.pager = pager
        if pager is None:
            self.pager = serial.Serial(port=port, baudrate=baud,
                                       timeout=timeout)
        self.arena_api = config_stuff
        self.status = {'alert_messages': 0,
                       'other_messages': 0,
                       'last_read_time': None}
        try:
            import pushover
            self.pushover = pushover.Client()
        except Exception:
            self.pushover = SilentPushover()

    @property
    def log(self):
        if self.config.get('silent'):
            return NullLogger()
        return Logger(self.verbose, self.config.get('lineFile'))

    def sleep_interval(self):
        interval = self.start_sleep_intervals[self.start_sleep_idx]
        if self.start_sleep_idx + 1 < len(self.start_sleep_intervals):
            self.start_sleep_idx += 1
        return interval

    def startup(self):
        try:
            self.arena_api.startup(self)
        except Exception as e:
            self.on_exception(e)
            self.need_sleep = self.sleep_interval()
            raise
        else:
            self.start_sleep_idx = 0
            self.needs_startup = False

    def main_once(self):
        if self.needs_startup:
            # report our IP to admin.
            self.send_addresses()
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
            # parse & handle the data that we read
            self.handle_serial_data(data)
        elif self.verbose:
            print('No data within timeout period')

        if self.messages:
            try:
                self.arena_api.log_messages(self, self.messages)
            except Exception as exception:
                self.on_exception(exception)
            else:
                self.messages = []
        
        try:
            self.arena_api.report(self)
        except Exception:
            self.needs_startup = True
            raise
        else:
            if self.verbose:
                print('Reported to Arena')
        
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
            if self.debug and alert['latitude'] is None:
                self.make_random_geo(alert)
            if self.verbose:
                read_page.show_alert_message(pager_message, alert)
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

    def on_alert_message(self, alert):
        self.messages.append({'ts' : str(datetime.now()),
                              'type' : 'alert',
                              'message' : alert['message']})
        headers = {"x-version": self.config['xver'],
                   "authorization": self.config['auth'],
                   "content-type": "application/x-www-form-urlencoded"}
        response = requests.post(self.config['pddUrl'],
                                 headers=headers,
                                 data=urllib.urlencode(alert))
        response.raise_for_status()
        self.status['alert_messages'] += 1

    def on_unhandled_message(self, message):
        self.messages.append({'ts' : str(datetime.now()),
                              'type' : 'pager_message',
                              'message' : message})
        self.status['other_messages'] += 1

    def on_exception(self, exception):
        exception_text = traceback.format_exception_only(type(exception),
                                                         exception)
        now = datetime.now()
        self.errors.setdefault(''.join(exception_text), []).append(
            {'ts' : str(now)})
        self.log.report_exception(now, exception)



class _Shutdown(BaseException):
    pass

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
