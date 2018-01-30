import pager2.schema as S
import pytest
import json
from base64 import b64decode
from datetime import datetime
from sqlalchemy import create_engine, select
from pager2.write import (write_startup, write_update,
                          write_report, write_messages, write_exception,
                          write_alerts)
from pager2.helpers import int_frombytes, int_bytes

TEST_IP = '116.101.115.116'

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    S.metadata.create_all(engine)
    return engine.connect()

def test_fresh_startup(db):
    cap = write_startup(db, TEST_IP, {
        'hostname' : 'test-server',
        'private_ip' : '127.0.0.1',
        'revision' : 'version awesome'
    })
    cap_decoded = b64decode(cap)
    cycle_id = int_frombytes(cap_decoded[32:])
    all_cycles = list(db.execute(select([S.pager_cycle])))
    assert len(all_cycles) == 1, "One pager_cycle should be saved on startup"

    cycles = list(db.execute(select([S.pager_cycle]).
                             where(S.pager_cycle.c.id == cycle_id)))
    assert len(cycles) == 1, ("Failed to retrieve pager_cycle after "
                              "write_startup saved it")


def test_stale_startup(db):
    db.execute(S.pager.insert({'public_ip' : TEST_IP}))
    cap = write_startup(db, TEST_IP, {
        'hostname' : 'test-server',
        'private_ip' : '127.0.0.1',
        'revision' : 'version awesome'
    })
    assert len(list(db.execute(select([S.pager.c.public_ip])))) == 1, (
        'Startup should not created pager object if one with that public '
        'ip already exists')
    cap_decoded = b64decode(cap)
    cycle_id = int_frombytes(cap_decoded[32:])
    all_cycles = list(db.execute(select([S.pager_cycle])))
    assert len(all_cycles) == 1, "One pager_cycle should be saved on startup"

    cycles = list(db.execute(select([S.pager_cycle]).
                             where(S.pager_cycle.c.id == cycle_id)))
    assert len(cycles) == 1, ("Failed to retrieve pager_cycle after "
                              "write_startup saved it")


def create_pager(db):
    data = {
        'hostname' : u'example.com',
        'private_ip' : u'127.0.0.1',
        'revision' : u'test'
    }

    pager_id = db.execute(S.pager.insert({'public_ip' : TEST_IP})
                      ).inserted_primary_key[0]

    start = datetime(2018, 1, 17, 16, 30)
    read = datetime(2018, 1, 17, 16, 39)
    
    start_data = {
        'pager_id' : pager_id,
        'salt' : u'*' * 32,
        'auth' : (u'9323c1cd4575a1a2b5ecf83d7c22a4446163671066f8b0d7a90'
                  u'3875f17ec4fc3'),
        'start_time' : start,
        'report_time' : read,
        'read_time' : read,
    }

    start_data.update(data)

    cycle_id = db.execute(S.pager_cycle.insert(start_data)
    ).inserted_primary_key[0]
    return pager_id, cycle_id


def test_save_report(db):
    _, cycle_id = create_pager(db)
    report = {'last_read_time' : '2018-01-17 16:46:54.228522'}
    write_report(db, cycle_id, report)
    (read_time,), = db.execute(select([S.pager_cycle.c.read_time]))
    assert str(read_time) == report['last_read_time']


def test_save_messages(db):
    _, cycle_id = create_pager(db)
    messages = [
        {'ts' : u'2018-01-17 16:40:16.111111',
         'type' : u'pager_message',
         'message' : u'There will be cake'},
        {'ts' : u'2018-01-17 16:40:33.333333',
         'type' : u'alert',
         'message' : u'82 098 @@ALERT Y0 x woo [resource]'},
        {'ts' : u'2018-01-17 16:46:22.333333',
         'type' : u'alert',
         'message' : u'x x @@ALERT F0 x G&SC1 message'},
    ]
    write_messages(db, cycle_id, messages)
    saved_messages = db.execute(
        select([
            S.general_message.c.timestamp,
            S.general_message.c.text,
            S.general_message.c.pager_cycle_id,
        ]).
        order_by(S.general_message.c.timestamp)
    )
    for index, (ts, text, pager_cycle_id), data in zip(
            xrange(3), saved_messages, messages):
        assert text == data['message']
        assert pager_cycle_id == cycle_id
    assert index == 2, "Not all messages saved?"


def test_save_alert_messages(db):
    _, cycle_id = create_pager(db)
    messages = [
        {'ts' : u'2018-01-17 16:40:33.333333',
         'type' : u'alert',
         'message' : u'82 098 @@ALERT Y0 x woo [resource]',
         'capCode' : u'000569192'},
        {'ts' : u'2018-01-17 16:46:22.333333',
         'type' : u'alert',
         'message' : u'x x @@ALERT F0 x G&SC1 message',
         'aircraftMsg' : 1,
         'assignmentArea' : u'TYLD3',
         'cadEvent' : u'F151210997',
         'capCode' : u'000569192',
         'coords' : u'718696',
         'dirRef' : u'SVC 6274 B11',
         'dirType' : u'SV',
         'incType' : u'G&S',
         'lat' : u'-37.2919713',
         'lon' : u'144.4262171',
         'msgType' : u'@@ALERT',
         'resource' : u'NEBRIA',
         'responseCode' : u'1'},
    ]
    write_alerts(db, cycle_id, messages)
    saved_messages = db.execute(
        select([
            S.alert_message.c.timestamp,
            S.alert_message.c.text,
            S.alert_message.c.pager_cycle_id,
            S.alert_message.c.details,
        ]).
        order_by(S.alert_message.c.timestamp)
    )

    ts, text, pager_cycle_id, data = saved_messages.fetchone()
    assert str(ts) == messages[0]['ts']
    assert text == messages[0]['message']
    assert pager_cycle_id == cycle_id
    assert data == '{"capCode": "000569192"}'

    ts, text, pager_cycle_id, data = saved_messages.fetchone()
    assert str(ts) == messages[1]['ts']
    assert text == messages[1]['message']
    assert pager_cycle_id == cycle_id

    expected_data = dict(messages[1])
    del expected_data['ts']
    del expected_data['type']
    del expected_data['message']
    assert json.loads(data) == expected_data

    saved_messages.close()


def test_save_errors(db):
    _, cycle_id = create_pager(db)
    write_exception(db, cycle_id, 'FooException: something', [
        {'ts': '2018-01-17 16:46:54.222222'},
        {'ts': '2018-01-17 16:44:54.111111'},
    ])
    (text, emt_id), = db.execute(select([
        S.error_message_text.c.text,
        S.error_message_text.c.id,
    ]))
    assert 'FooException: something' == text
    saved_exceptions = db.execute(select([
        S.error_message.c.error_message_text_id,
        S.error_message.c.pager_cycle_id,
    ]))
    for i, (emti, pcid) in enumerate(saved_exceptions):
        assert emti == emt_id
        assert pcid == cycle_id
    assert i == 1, "Not all exception occurrences saved?"

