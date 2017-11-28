from __future__ import print_function
import os
import sys
import traceback
from datetime import datetime

MEGABYTE = 1 << 20

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
        if os.stat(self.line_file).st_size > MEGABYTE:
            os.remove(self.line_file)
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

    def report_server_error(self, data):
        print(bcolors.WARNING + "SERVER ERROR:")
        print(datetime.now().isoformat())
        for error in data['errors']:
            print('  ', error)
        print(bcolors.ENDC)
        print("ADDITIONAL INFO:")
        for info in data['info']:
            print('  ', info)

    def report_exception(self, now, e):
        print(bcolors.WARNING + "ERROR....")
        print(now.isoformat())
        traceback.print_exc()#limit=None if self.verbose else 1)
        print(bcolors.ENDC)


class NullLogger(object):
    def pager_log_all(self, line):
        pass

    def fail_and_exit(self, text):
        sys.exit(text)

    def report_server_error(self, data):
        pass

    def report_exception(self, now, e):
        pass
