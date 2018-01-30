from google.appengine.ext import ndb
from google.appengine.ext.ndb import Key

class Report(ndb.Model):
    "Models a report from a pager."
    public_ip = ndb.StringProperty()
    report_time = ndb.DateTimeProperty()
    last_read_time = ndb.DateTimeProperty()
    alert_messages = ndb.IntegerProperty()
    other_messages = ndb.IntegerProperty()

class Status(ndb.Model):
    "Models the details of a pager."
    public_ip = ndb.StringProperty()
    report_time = ndb.DateTimeProperty()
    private_ip = ndb.StringProperty()
    revision = ndb.StringProperty()
    hostname = ndb.StringProperty()

class PagerException(ndb.Model):
    "One exception report"
    report_time = ndb.DateTimeProperty()
    traceback = ndb.TextProperty()

class Message(ndb.Model):
    "One pager message"
    report_time = ndb.DateTimeProperty()
    #message = ndb.BlobProperty()
    message = ndb.TextProperty()

class PushoverUser(ndb.Model):
    name = ndb.StringProperty()

class PushoverConfig(ndb.Model):
    name = ndb.StringProperty()
    user_key = ndb.StringProperty()

