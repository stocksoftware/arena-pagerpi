import serial
import signal
import page_log

from datetime import datetime
from read_page import handle_serial_data


class PagerPI(object):
    debug = False
    quiet = False
    stop = False
    start_sleep_idx = 0
    needs_startup = True
    start_sleep_intervals = [5, 15, 30, 60, 120, 240]

    def __init__(self, port='/dev/serial0', baud=9600, timeout=5.*60):
        self.pager = serial.Serial(port=port, baudrate=baud, timeout=timeout)

    def sleep_interval(self):
        interval = self.start_sleep_intervals[self.start_sleep_idx]
        self.start_sleep_idx += 1
        if self.start_sleep_idx + 1 < len(start_sleep_intervals):
            self.start_sleep_idx += 1
        return interval

    def startup(self):
        try:
            config_stuff.startup()
        except Exception as e:
            page_log.report_exception(e)
            self.need_sleep = self.sleep_interval()
            raise
        else:
            self.start_sleep_idx = 0
            self.needs_startup = False

    def main_once(self):
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
            STATUS['last_read_time'] = datetime.now()
            page_log.pager_log_all(data)
            
        # parse & handle the data that we read
        handle_serial_data(self, data)
        try:
            config_stuff.report()
        except Exception:
            needs_startup = True
            raise
        
    def main(self):
        while not self.stop:
            try:
                self.main_once()
            except Exception as exception:
                page_log.report_exception(exception)
            if self.need_sleep is not None:
                time.sleep(self.need_sleep)
                self.need_sleep = None

    def shutdown_handler(self, signum, frame):
        page_log.stop_logs()
        raise _SHUTDOWN


class _Shutdown(BaseException):
    pass

_SHUTDOWN = _Shutdown("TERM signal received")


def main(debug=False, quiet=False):
    if not quiet:
        print "PagerTest Startup v020"
        print datetime.now().isoformat()
    page_log.start_logs()
    try:
        pagerpi = PagerPI()
        pagerpi.debug = debug
        pagerpi.quiet = quiet
        signal.signal(signal.SIGTERM, pagerpi.shutdown_handler)
        pagerpi.main()
    except _Shutdown:
        pass


if __name__ == '__main__':
    main()
