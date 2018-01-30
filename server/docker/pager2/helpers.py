from datetime import datetime
from random import SystemRandom
from base64 import b64encode, b64decode
from hashlib import sha256 as sha
from json import load
import traceback
import logging
import jinja2
import os.path


RANDOM = SystemRandom()


class AuthException(Exception):
    pass


def get_auth(auth, salt):
    return sha(auth + salt).hexdigest().decode('ascii')


def startup_cap_check(cap_path):
    cap = config.get_config('service_capability')
    if not is_equal(cap, cap_path):
        raise AuthException("please supply a valid service capability")


def view_cap_check(cap_path):
    cap = config.get_config('status_capability')
    if not is_equal(cap, cap_path):
        raise AuthException("please supply a valid status capability")


def getarg(request, name, default=None):
    xs = request.args.get(name, [])
    if xs:
        return xs[0]
    return default


class _Config(object):
    CAP_PATH = '/pager-data/pager_config.json'
    config = None
    _instance = None
    def get_config(self, key):
        if self.config is None:
            with open(self.CAP_PATH) as f:
                self.config = load(f)
        return self.config[key]


config = _Config()


def dt(string):
    "Read a datetime from a string"
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")


def int_bytes(k, n):
    """Pack integer k into a big-endian bytearray of length n
    """
    return bytearray((k >> (j * 8)) & 0xff
                     for j in xrange(n - 1, -1, -1))


def int_frombytes(s):
    """Read an integer from the big-endian bytesequence s
    """
    result = 0
    for b in bytearray(s):
        result <<= 8
        result |= b
    return result


def random_bytes(n):
    """Generate n random bytes using the system prng
    """
    number = RANDOM.getrandbits(n * 8)
    return bytearray((number >> (i * 8)) & 0xff for i in xrange(32))


def is_equal(s, t):
    """Constant-time string equal function
    """
    if len(s) == len(t):
        result = 1
    else:
        result = 0
        t = s
    for x, y in zip(s, t):
        result &= int(x == y)
    return result

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
