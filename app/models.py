from app import db, app
from passlib.apps import custom_app_context as pwd_context
import flask.ext.whooshalchemy as whooshalchemy
import string
import random

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    offers = db.relationship('Offer', backref='author', lazy='dynamic')
    user_name = db.Column(db.String(128))
    surname = db.Column(db.String(128))
    street = db.Column(db.String(128))
    building_number = db.Column(db.String(16))
    door_number = db.Column(db.String(16))
    city = db.Column(db.String(32))
    zipcode = db.Column(db.String(16))
    country = db.Column(db.String(32))
    phone = db.Column(db.String(16))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), default=2)
    to_delete = db.Column(db.Boolean, default=0)


    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<User %r>' % (self.nickname)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    offers = db.relationship('Offer', backref='category', lazy='dynamic')

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<Category %r>' % (self.name)

class Offer(db.Model):
    __searchable__ = ['name', 'body']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    title = db.Column(db.String(128))
    book_author = db.Column(db.String(128))
    price = db.Column(db.Float)
    shipping = db.Column(db.Float)
    count = db.Column(db.Integer)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    to_delete = db.Column(db.Boolean, default=0)

    def is_valid(self):
        if self is not None and self.count > 0:
            return True
        else:
            return False

    def is_available(self, count):
        if self is not None and self.count-count >= 0:
            return True
        else:
            return False

    def __repr__(self):
        return '<Offer %r>' % (self.body)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), index=True, unique=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    id_from = db.Column(db.Integer)
    id_to = db.Column(db.Integer)
    transaction_id = db.Column(db.Integer)
    type = db.Column(db.Boolean)
    body = db.Column(db.String(140))
    to_delete = db.Column(db.Boolean, default=0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    offer_id = db.Column(db.Integer, db.ForeignKey('offer.id'))
    count = db.Column(db.Integer)
    price = db.Column(db.Float)
    hash_link = db.Column(db.String(128))
    is_finalised = db.Column(db.Boolean)
    is_sent = db.Column(db.Boolean)
    is_commented = db.Column(db.Boolean)
    to_delete = db.Column(db.Boolean, default=0)

    def hash_generator(self, size=32, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def __repr__(self):
        return '<Transaction %r>' % (self.id)

whooshalchemy.whoosh_index(app, Offer)

#Archive----------------------------------------------------------
class Archive_transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer)
    offer_id = db.Column(db.Integer)
    count = db.Column(db.Integer)
    price = db.Column(db.Float)
    hash_link = db.Column(db.String(128))
    is_finalised = db.Column(db.Boolean)
    is_sent = db.Column(db.Boolean)
    is_commented = db.Column(db.Boolean)
    
class Archive_offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer)
    name = db.Column(db.String(128))
    title = db.Column(db.String(128))
    book_author = db.Column(db.String(128))
    price = db.Column(db.Float)
    shipping = db.Column(db.Float)
    count = db.Column(db.Integer)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    category_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)

class Archive_user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    nickname = db.Column(db.String(32))
    email = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    user_name = db.Column(db.String(128))
    surname = db.Column(db.String(128))
    street = db.Column(db.String(128))
    building_number = db.Column(db.String(16))
    door_number = db.Column(db.String(16))
    city = db.Column(db.String(32))
    zipcode = db.Column(db.String(16))
    country = db.Column(db.String(32))
    phone = db.Column(db.String(16))
    role_id = db.Column(db.Integer)