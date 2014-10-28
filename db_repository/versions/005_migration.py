from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
user = Table('user', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String(length=32)),
    Column('email', String(length=128)),
    Column('password_hash', String(length=128)),
    Column('street', String(length=128)),
    Column('building_number', String(length=16)),
    Column('door_number', String(length=16)),
    Column('city', String(length=32)),
    Column('zipcode', String(length=16)),
    Column('country', String(length=32)),
    Column('phone', String(length=16)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['user'].columns['building_number'].create()
    post_meta.tables['user'].columns['city'].create()
    post_meta.tables['user'].columns['country'].create()
    post_meta.tables['user'].columns['door_number'].create()
    post_meta.tables['user'].columns['nickname'].create()
    post_meta.tables['user'].columns['phone'].create()
    post_meta.tables['user'].columns['street'].create()
    post_meta.tables['user'].columns['zipcode'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['user'].columns['building_number'].drop()
    post_meta.tables['user'].columns['city'].drop()
    post_meta.tables['user'].columns['country'].drop()
    post_meta.tables['user'].columns['door_number'].drop()
    post_meta.tables['user'].columns['nickname'].drop()
    post_meta.tables['user'].columns['phone'].drop()
    post_meta.tables['user'].columns['street'].drop()
    post_meta.tables['user'].columns['zipcode'].drop()
