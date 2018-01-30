from sqlalchemy import MetaData
from sqlalchemy.schema import (Column, Table, ForeignKey)
from sqlalchemy.types import Integer, DateTime, String

metadata = MetaData()

pager = Table(
    'pager', metadata,
    Column('id', Integer, primary_key=True),
    Column('public_ip', String(16), nullable=False),
)

pager_cycle = Table(
    'pager_cycle', metadata,
    Column('id', Integer, primary_key=True),
    Column('pager_id', Integer, ForeignKey(pager.c.id), nullable=False),
    Column('auth', String(32), nullable=False),
    Column('salt', String(32), nullable=False),
    Column('start_time', DateTime, nullable=False),
    Column('report_time', DateTime, nullable=False),
    Column('read_time', DateTime),
    Column('private_ip', String(16), nullable=False),
    Column('hostname', String(30), nullable=False),
    Column('revision', String(30), nullable=False),
)

general_message = Table(
    'pager_message', metadata,
    Column('id', Integer, primary_key=True),
    Column('pager_cycle_id', Integer, ForeignKey(pager_cycle.c.id),
           nullable=False),
    Column('timestamp', DateTime, nullable=False),
    Column('text', String(250), nullable=False),
)

alert_message = Table(
    'alert_message', metadata,
    Column('id', Integer, primary_key=True),
    Column('pager_cycle_id', Integer, ForeignKey(pager_cycle.c.id),
           nullable=False),
    Column('timestamp', DateTime, nullable=False),
    Column('text', String(250), nullable=False),
    Column('details', String(1000), nullable=False),
)

error_message_text = Table(
    'error_message_text', metadata,
    Column('id', Integer, primary_key=True),
    Column('text', String(1000), nullable=False),
)

error_message = Table(
    'error_message', metadata,
    Column('id', Integer, primary_key=True),
    Column('pager_cycle_id', Integer, ForeignKey(pager_cycle.c.id),
           nullable=False),
    Column('timestamp', DateTime, nullable=False),
    Column('error_message_text_id', Integer,
           ForeignKey(error_message_text.c.id), nullable=False),
)
