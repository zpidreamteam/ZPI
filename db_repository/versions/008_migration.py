from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
transaction = Table('transaction', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('timestamp', DateTime),
    Column('user_id', Integer),
    Column('offer_id', Integer),
    Column('count', Integer),
    Column('price', Float),
    Column('hash_link', String(length=128)),
    Column('is_finalised', Boolean),
)

offer = Table('offer', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=128)),
    Column('title', String(length=128)),
    Column('author', String(length=128)),
    Column('price', Float),
    Column('shipping', Float),
    Column('count', Integer),
    Column('body', String(length=140)),
    Column('timestamp', DateTime),
    Column('category_id', Integer),
    Column('user_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['transaction'].create()
    post_meta.tables['offer'].columns['author'].create()
    post_meta.tables['offer'].columns['shipping'].create()
    post_meta.tables['offer'].columns['title'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['transaction'].drop()
    post_meta.tables['offer'].columns['author'].drop()
    post_meta.tables['offer'].columns['shipping'].drop()
    post_meta.tables['offer'].columns['title'].drop()
