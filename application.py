from __future__ import print_function

import config_stuff
import serial
import signal
import requests
import time
import traceback

from subprocess import check_output
from datetime import datetime
from read_page import handle_serial_data
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
        self.config = {}
        self.pager = pager
        if pager is None:
            self.pager = serial.Serial(port=port, baudrate=baud,
                                       timeout=timeout)
        self.arena_api = config_stuff
        self.status = {'errors': [],
                       'alert_messages': 0,
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
            self.messages.append({'ts' : str(datetime.now()),
                                  'message' : data})
            self.log.pager_log_all(data)
            # parse & handle the data that we read
            handle_serial_data(self, data)
        elif self.verbose:
            print('No data within timeout period')

        try:
            while self.messages:
                message = self.messages.pop(0)
                self.arena_api.log_message(self, message)
        except Exception:
            pass
        
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

    def on_alert_message(self, message):
        headers = {"x-version": self.config['xver'],
                   "authorization": self.config['auth']}
        response = requests.post(self.config['pddUrl'],
                                 headers=headers, data=message)
        response.raise_for_status()

    def on_exception(self, exception):
        exception_text = traceback.format_exception_only(type(exception),
                                                         exception)
        now = datetime.now()
        self.status['errors'].append({'ts' : now.isoformat(),
                                      'message' : exception_text})
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
