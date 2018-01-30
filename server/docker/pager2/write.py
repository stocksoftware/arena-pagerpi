from pager2.schema import (pager, pager_cycle, general_message,
                           alert_message,
                           error_message_text, error_message)
from datetime import datetime
from read import get_auth
from base64 import b64encode
from sqlalchemy import select
from pager2.helpers import dt, random_bytes, int_bytes, startup_cap_check
import traceback
import logging
import json


def write_startup(db, public_ip, data):
    for pager_id, in db.execute(select([pager.c.id]).where(
            pager.c.public_ip == public_ip)):
        break
    else:
        pager_id, = db.execute(
            pager.insert({'public_ip' : public_ip})
        ).inserted_primary_key
    now = datetime.now()
    salt = random_bytes(32)
    auth = random_bytes(32)
    data = {
        'pager_id' : pager_id,
        'salt' : b64encode(salt),
        'auth' : get_auth(auth, salt),
        'start_time' : now,
        'report_time' : now,
        'read_time' : None,
        'hostname' : data['hostname'].decode('utf-8'),
        'private_ip' : data['ip_address'].decode('ascii'),
        'revision' : data['revision'].decode('utf-8')
    }
    pcid = db.execute(pager_cycle.insert(data)).inserted_primary_key[0]
    return b64encode(auth + int_bytes(pcid, 8))


def write_update(db, pager_cycle_id, report, errors, messages):
    result = {'errors' : []}
    def _exception(e, name):
        logging.exception(e.message)
        result['errors'].append('Unable to save %s: %s' % (
            name,
            ''.join(traceback.format_exception_only(type(e), e))))
        
    now = datetime.now()
    try:
        write_report(db, pager_cycle_id, report)
    except Exception as e:
        _exception(e,'report')

    try:
        for tb, timestamps in errors:
            write_exception(db, pager_cycle_id, tb, timestamps)
    except Exception as e:
        _exception(e, 'exceptions')

    try:
        general_messages = [msg for msg in messages
                            if msg['type'] != 'alert']
        if general_messages:
            write_messages(db, pager_cycle_id, general_messages)
    except Exception as e:
        _exception(e, 'messages')

    try:
        alert_messages = [msg for msg in messages
                          if msg['type'] == 'alert']
        if alert_messages:
            write_alerts(db, pager_cycle_id, alert_messages)
    except Exception as e:
        _exception(e, 'alerts')
    return result


def write_report(db, pager_cycle_id, data):
    now = datetime.now()
    db.execute(pager_cycle.update().
               where(pager_cycle.c.id == pager_cycle_id).
               values(report_time=now,
                      read_time=dt(data['last_read_time'])))


def write_messages(db, pager_cycle_id, data):
    db.execute(
        general_message.insert(),
        [{'text' : msg['message'],
          'pager_cycle_id' : pager_cycle_id,
          'timestamp' : dt(msg['ts'])} for msg in data]
    )


NON_ALERT_FIELDS = set(['message', 'ts', 'type'])

def _alert_structure(pager_cycle_id, alert):
    extra_data = dict((k, v) for k, v in alert.items()
                      if k not in NON_ALERT_FIELDS)
    return {
        'pager_cycle_id' : pager_cycle_id,
        'timestamp' : dt(alert['ts']),
        'text' : alert['message'],
        'details' : json.dumps(extra_data)[:1000],
    }


def write_alerts(db, pager_cycle_id, alerts):
    db.execute(alert_message.insert(), [
        _alert_structure(pager_cycle_id, alert) for alert in alerts
    ])


def write_exception(db, pager_cycle_id, traceback, timestamps):
    traceback = traceback[:1000]
    text_ids = list(db.execute(error_message_text.
                               select(error_message_text.c.id).
                               where(error_message_text.c.text == traceback)))
    if not text_ids:
        text_ids = db.execute(
            error_message_text.insert({'text' : traceback})
        ).inserted_primary_key

    db.execute(
        error_message.insert(),
        [{
            'error_message_text_id' : text_ids[0],
            'timestamp' : dt(ts['ts']),
            'pager_cycle_id' : pager_cycle_id
        } for ts in timestamps]
    )
