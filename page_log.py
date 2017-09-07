import sys
from datetime import datetime
from config_stuff import STATUS

outFileName = '/home/pi/pagerOut020.txt'
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


def pager_log_json(params):
    with open(outFileName, 'a') as f:
        f.write(datetime.now().isoformat())
        f.write("\n")
        json.dump(params, f, indent=4)
        f.write("\n")


def pager_log_all(line):
    with open(pagerLineFile, 'a') as f:
        f.write(datetime.now().isoformat())
        f.write("\n")
        f.write(line)
        f.write("\n")


def start_logs():
    now = datetime.now()
    with open(outFileName, 'a') as f:
        f.write(now.isoformat())
        f.write("\nSTARTUP\n")

    with open(pagerLineFile, 'a') as f:
        f.write(now.isoformat())
        f.write("\nSTARTUP\n")


def stop_logs():
    now = datetime.now()
    with open(outFileName, 'a') as f:
        f.write(now.isoformat())
        f.write("\nSHUTDOWN\n")

    with open(pagerLineFile, 'a') as f:
        f.write(now.isoformat())
        f.write("\nSHUTDOWN\n")


def fail_and_exit(text):
    """Log failure for next time we start, and exit the program.
    """
    with open(FAIL_LOG, 'a') as f:
        f.write("%s\n" % datetime.now())
        f.write(text)
        f.write("\n")
    sys.exit(text)

def report_exception(e):
    now = datetime.now()
    STATUS['errors'].append({'ts' : now.isoformat(), 'message', e.message})
    print bcolors.WARNING + "ERROR...."
    print now.isoformat()
    print e 
    print bcolors.ENDC

def report_error(message):
    now = datetime.now()
    STATUS['errors'].append({'ts' : now.isoformat(), 'message', message})
    print bcolors.WARNING + "ERROR...."
    print now.isoformat()
    print message
    print bcolors.ENDC

