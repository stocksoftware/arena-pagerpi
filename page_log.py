from __future__ import print_function
import sys
import traceback
from datetime import datetime

pagerLineFile = '/home/pi/pager_lines.txt'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger(object):
    def __init__(self, verbose, line_file):
        self.verbose = verbose
        self.line_file = line_file

    def pager_log_all(self, line):
        if self.line_file is None:
            return
        with open(self.line_file, 'a') as f:
            f.write(datetime.now().isoformat())
            f.write("\n")
            f.write(line)
            f.write("\n")

    def fail_and_exit(self, text):
        """Log failure for next time we start, and exit the program.
        """
        print(datetime.now())
        sys.exit(text)

    def report_exception(self, now, e):
        print(bcolors.WARNING + "ERROR....")
        print(now.isoformat())
        traceback.print_exc(limit=None if app.verbose else 1)
        print(bcolors.ENDC)

# def report_error(app, message):
#     now = datetime.now()
#     app.status['errors'].append({'ts' : now.isoformat(),
#                                  'message' : message})
#     print bcolors.WARNING + "ERROR...."
#     print now.isoformat()
#     print message
#     print bcolors.ENDC

class NullLogger(object):
    def pager_log_all(self, line):
        pass

    def fail_and_exit(self, text):
        sys.exit(text)

    def report_exception(self, now, e):
        pass
