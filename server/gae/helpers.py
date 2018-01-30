#import cgi
import os
import base64
import jinja2
from datetime import datetime


# class CGIMap(object):
#     def __init__(self, m):
#         self.m = m
#     def __getitem__(self, key):
#         value = self.m[key]
#         return cgi.escape(str(value))


# class CGIAttrMap(object):
#     def __init__(self, m):
#         self.m = m
#     def __getitem__(self, key):
#         value = getattr(self.m, key)
#         return cgi.escape(str(value))


def is_equal(a, b):
    "Constant time string equality"
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def parse_dt(s):
    if not s:
        return None
    s, _, _ = s.partition('.')
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def new_capability():
    return base64.urlsafe_b64encode(os.urandom(24)).rstrip('=')


JINJA = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def jinja_filter(f):
    JINJA.filters[f.__name__] = f
    return f

    
@jinja_filter
def ago(dt):
    time_diff = int((datetime.now() - dt['report_time']).total_seconds())
    td_seconds = time_diff % 60
    td_minutes = time_diff // 60
    
    if td_minutes:
        return "%s minutes ago" % (td_minutes,)
    return "%s seconds ago" % (td_seconds,)


@jinja_filter
def status_style(status):
    time_diff = int((datetime.now() - status['report_time']).total_seconds())
    if time_diff > (5 * 60):
        return "color:red;"
    else:
        return "color:green;"
