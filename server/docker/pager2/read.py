from pager2.schema import (pager, pager_cycle, general_message,
                           alert_message,
                           error_message_text, error_message)
from pager2.helpers import (get_auth, AuthException, config, int_frombytes,
                            is_equal)
from sqlalchemy import select, union_all
from datetime import datetime
from base64 import b64decode
from hashlib import sha256 as sha
from json import load


def get_pager_cycle(db, key):
    key_number = b64decode(key)
    if len(key_number) > 100:
        raise AuthException("please supply a valid pager key")
    pcid = int_frombytes(key_number[-8:])
    auth = key_number[:-8]
    res = db.execute(
        select([pager_cycle.c.auth, pager_cycle.c.salt]).
        where(pager_cycle.c.id == pcid))
    for db_auth, salt in res:
        if is_equal(db_auth, get_auth(auth, b64decode(salt))):
            return pcid
        break
    raise AuthException("please supply a valid pager key")
        

def select_dict(db, sel):
    return [dict(row.items()) for row in db.execute(sel)]


def get_pagers(db):
    pagers = []
    by_cycle_id = {}
    for (public_ip, cycle_id, start_time, report_time, read_time,
         private_ip, hostname, revision) in db.execute(
             select([pager.c.public_ip,
                     pager_cycle.c.id,
                     pager_cycle.c.start_time,
                     pager_cycle.c.report_time,
                     pager_cycle.c.read_time,
                     pager_cycle.c.private_ip,
                     pager_cycle.c.hostname,
                     pager_cycle.c.revision]).
             where(pager.c.id == pager_cycle.c.pager_id)):
        one_pager = {
            'hostname' : (hostname or '').strip() or '<unnamed>',
            'public_ip' : public_ip,
            'private_ip' : private_ip,
            'report_time' : report_time,
            'read_time' : read_time,
            'revision' : revision,
            'messages' : []
        }
        pagers.append(one_pager)
        by_cycle_id[cycle_id] = one_pager

    for cycle_id, timestamp, text in db.execute(
        union_all(select([general_message.c.pager_cycle_id,
                          general_message.c.timestamp,
                          general_message.c.text]),
                  select([alert_message.c.pager_cycle_id,
                          alert_message.c.timestamp,
                          alert_message.c.text]),
                  select([error_message.c.pager_cycle_id,
                          error_message.c.timestamp,
                          error_message_text.c.text]).
                  where(error_message.c.error_message_text_id ==
                        error_message_text.c.id)
              ).order_by(general_message.c.timestamp)):
        try:
            messages = by_cycle_id[cycle_id]['messages']
        except KeyError:
            continue
        messages.append({'ts' : timestamp,'message' : text, 'type' : ''})

    return pagers
