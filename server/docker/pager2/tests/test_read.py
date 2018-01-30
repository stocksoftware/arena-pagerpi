import pager2.schema as S
import pytest
from pager2.read import get_pagers
from datetime import datetime
from sqlalchemy import create_engine, select

TEST_IP_1 = '116.101.115.116'
TEST_IP_2 = '73.80.95.49'

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    S.metadata.create_all(engine)
    return engine.connect()

def dt_minutes(min, sec=0):
    return datetime(2018, 4, 5, 14, min, sec)

def dt_minutes_old(min, sec=0):
    return datetime(2018, 1, 30, 13, min, sec)

def ins(db, table, data):
    return db.execute(table.insert(), data).inserted_primary_key[0]

def test_get_pagers(db):
    p1 = ins(db, S.pager, {'public_ip' : TEST_IP_1})
    p2 = ins(db, S.pager, {'public_ip' : TEST_IP_2})
    pc1 = ins(db, S.pager_cycle,
              {'pager_id' : p1, 'auth' : '', 'salt' : '',
               'start_time' : dt_minutes_old(15, 50),
               'read_time' : dt_minutes_old(16, 7),
               'report_time' : dt_minutes_old(16, 26),
               'private_ip' : '10.0.0.14',
               'revision' : 'x',
               'hostname' : 'pi0'})
    pc2 = ins(db, S.pager_cycle, 
              {'pager_id' : p1, 'auth' : '', 'salt' : '',
               'start_time' : datetime(2018, 4, 5, 2, 0, 0),
               'read_time' : dt_minutes(28),
               'report_time' : dt_minutes(30),
               'private_ip' : '10.0.0.16',
               'revision' : 'x',
               'hostname' : 'pi0'})
    
    pc3 = ins(db, S.pager_cycle, 
              {'pager_id' : p2, 'auth' : '', 'salt' : '',
               'start_time' : dt_minutes(0),
               'read_time' : dt_minutes(28),
               'report_time' : dt_minutes(30),
               'private_ip' : '10.0.0.14',
               'revision' : 'x',
               'hostname' : 'pi3'})

    db.execute(S.general_message.insert(), [
        {'pager_cycle_id' : pc1,
         'timestamp' : dt_minutes_old(16, 8), 'text' : 'Hello?'},
        {'pager_cycle_id' : pc2, 'timestamp' : dt_minutes(25),
         'text' : 'Are you still there?'},
    ])

    db.execute(S.alert_message.insert(), [
        {'pager_cycle_id' : pc2, 'timestamp' : dt_minutes(26),
         'text' : 'Could you come over here?', 'details' : '{}'},
        {'pager_cycle_id' : pc3, 'timestamp' : dt_minutes(25),
         'text' : 'There you are', 'details' : '{"bullets":5}'},
    ])

    error_message = ins(db, S.error_message_text,
                        {'text' : 'Nothing happens'})

    db.execute(S.error_message.insert(), [
        {'pager_cycle_id' : pc3, 'timestamp' : dt_minutes(27),
         'error_message_text_id' : error_message},
        {'pager_cycle_id' : pc1, 'timestamp' : dt_minutes_old(16, 9),
         'error_message_text_id' : error_message},
    ])

    data = get_pagers(db)

    cycle_0 = [p for p in data
               if p['hostname'] == 'pi0' and p['private_ip'] == '10.0.0.14']
    cycle_1 = [p for p in data
               if p['hostname'] == 'pi0' and p['private_ip'] == '10.0.0.16']
    cycle_2 = [p for p in data if p['hostname'] == 'pi3']

    assert cycle_0
    assert cycle_1
    assert cycle_2

    assert cycle_0[0]['messages'] == [
        {'ts': dt_minutes_old(16, 8), 'message': 'Hello?', 'type': ''},
        {'ts': dt_minutes_old(16, 9), 'message': 'Nothing happens',
         'type': ''},
    ]

    assert cycle_1[0]['messages'] == [
        {'ts' : dt_minutes(25),
         'message' : u'Are you still there?',
         'type': ''},
        {'ts': dt_minutes(26),
         'message': 'Could you come over here?',
         'type': ''},
    ]

    assert cycle_2[0]['messages'] == [
        {'ts': dt_minutes(25), 'message': 'There you are',
         'type': ''},
        {'ts': dt_minutes(27), 'message': 'Nothing happens',
         'type': ''},
    ]
