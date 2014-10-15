from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField
from wtforms.validators import DataRequired

class LoginForm(Form):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class RegisterForm(Form):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    password_repeat = PasswordField('password_repeat', validators=[DataRequired()])
    street = StringField('street', validators=[DataRequired()])
    building_number = StringField('building_number', validators=[DataRequired()])
    door_number = StringField('door_number', validators=[DataRequired()])
    city = StringField('city', validators=[DataRequired()])
    zipcode = StringField('zipcode', validators=[DataRequired()])
    country = StringField('country', validators=[DataRequired()])
    phone = StringField('phone', validators=[DataRequired()])