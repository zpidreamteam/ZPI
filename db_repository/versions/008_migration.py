from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
transaction = Table('transaction', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('timestamp', DATETIME),
    Column('user_id', INTEGER),
    Column('offer_id', INTEGER),
    Column('count', INTEGER),
    Column('price', FLOAT),
    Column('hash_link', VARCHAR(length=128)),
    Column('is_finalised', BOOLEAN),
)

upload = Table('upload', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', Unicode(length=255), nullable=False),
    Column('url', Unicode(length=255), nullable=False),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['transaction'].drop()
    post_meta.tables['upload'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['transaction'].create()
    post_meta.tables['upload'].drop()
