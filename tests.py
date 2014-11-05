#!flask/bin/python
import os
import unittest
from datetime import datetime, timedelta

from config import basedir
from app import app, db
from app.models import User, Category, Offer

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_user(self):
        u = User(email='john@example.com')
        db.session.add(u)
        db.session.commit()
        assert u.is_authenticated() is True
        assert u.is_active() is True
        assert u.is_anonymous() is False
        assert u.id == int(u.get_id())

    def test_category(self):
        u = User(email='john@example.com')
        c = Category(name = 'matematyka')
        db.session.add(u)
        db.session.add(c)
        db.session.commit()

        o = Offer(name = 'Analiza matematycza 1.0', price = 24.0, count = 20,
                  body = 'to jest przykladowy opis ksiazki', timestamp = datetime.utcnow(),
                  author = u, category = c
            )
        db.session.add(o)
        db.session.commit()

    def test_offer(self):
        u = User(email='john@example.com')
        c1 = Category(name = 'matematyka')
        c2 = Category(name = 'fizyka')
        db.session.add(u)
        db.session.add(c1)
        db.session.add(c2)
        db.session.commit()
        o1 = Offer(name = 'Analiza matematycza 1.0', price = 24.0, count = 20,
                  body = 'to jest przykladowy opis ksiazki', timestamp = datetime.utcnow(),
                  author = u, category = c1
            )
        o2 = Offer(name = 'Analiza matematycza 1.0', price = 20.0, count = 1,
                  body = 'to jest inny przykladowy opis ksiazki', timestamp = datetime.utcnow(),
                  author = u, category = c1
            )
        db.session.add(o1)
        db.session.add(o2)
        db.session.commit()

        assert len(Category.query.all()) == 2


if __name__ == '__main__':
    unittest.main()