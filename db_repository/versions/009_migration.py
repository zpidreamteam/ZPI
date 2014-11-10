from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
offer = Table('offer', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=128)),
    Column('price', FLOAT),
    Column('count', INTEGER),
    Column('body', VARCHAR(length=140)),
    Column('timestamp', DATETIME),
    Column('category_id', INTEGER),
    Column('user_id', INTEGER),
    Column('author', VARCHAR(length=128)),
    Column('shipping', FLOAT),
    Column('title', VARCHAR(length=128)),
)

offer = Table('offer', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=128)),
    Column('title', String(length=128)),
    Column('book_author', String(length=128)),
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
    pre_meta.tables['offer'].columns['author'].drop()
    post_meta.tables['offer'].columns['book_author'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['offer'].columns['author'].create()
    post_meta.tables['offer'].columns['book_author'].drop()
