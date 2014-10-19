from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired
from models import Category

class LoginForm(Form):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class RegisterForm(Form):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    password_repeat = PasswordField('password_repeat', validators=[DataRequired()])


class OfferForm(Form):
    name = StringField('name', validators=[DataRequired()])
    price = StringField('price', validators=[DataRequired()])
    count = FloatField('count', validators=[DataRequired()])
    body = TextAreaField('body', validators=[DataRequired()])
    category = SelectField('category', choices=[(c.id, c.name) for c in Category.query.all()])
