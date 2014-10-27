from app import db
from passlib.apps import custom_app_context as pwd_context

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    offers = db.relationship('Offer', backref='author', lazy='dynamic')
    street = db.Column(db.String(128))
    building_number = db.Column(db.String(16))
    door_number = db.Column(db.String(16))
    city = db.Column(db.String(32))
    zipcode = db.Column(db.String(16))
    country = db.Column(db.String(32))
    phone = db.Column(db.String(16))

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

    def __repr__(self):
        return '<Category %r>' % (self.name)

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    price = db.Column(db.Float)
    count = db.Column(db.Integer)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Offer %r>' % (self.body)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    offer_id = db.Column(db.Integer, db.ForeignKey('offer.id'))
    price = db.Column(db.Float)
    hash_link = db.Column(db.String(128))
    is_finalised = db.Column(db.Boolean)

    def __repr__(self):
        return '<Transaction %r>' % (self.id)