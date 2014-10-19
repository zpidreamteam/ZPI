from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, FloatField, SelectField, IntegerField
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
    price = FloatField('price', validators=[DataRequired()])
    count = IntegerField(validators=[DataRequired()])
    body = TextAreaField('body', validators=[DataRequired()])
    category_id = SelectField('category', coerce=int)