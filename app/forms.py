from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, FloatField, SelectField, IntegerField, TextField, RadioField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from models import Category

class LoginForm(Form):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class RegisterForm(Form):
    password = PasswordField('password', validators=[DataRequired(), Length(min=6, message="Podane haslo jest za krotkie"), EqualTo('password_repeat', message="Podane hasla musza byc takie same")])
    email = StringField('email', validators=[DataRequired(), Email(message="Prosze podac poprawny adres email"), Length(max=128, message="Podany adres email jest za dlugi")])
    nickname = StringField('nickname', validators=[DataRequired(), Length(min=3, max=32, message="Nickname musi skladac sie z minimalnie 3 a maksymalnie 32 znakow")])
    password_repeat = PasswordField('password_repeat', validators=[DataRequired()])
    user_name = StringField('user_name', validators=[DataRequired(), Length(max=32, message="Podane imie jest za dlugie")])
    surname = StringField('surname', validators=[DataRequired(), Length(max=32, message="Podane nazwisko jest za dlugie")])
    street = StringField('street', validators=[DataRequired(), Length(max=128, message="Podana nazwa ulicy jest za dluga")])
    building_number = StringField('building_number', validators=[DataRequired(), Length(max=16, message="Podany numer budynku jest za dlugi")])
    door_number = StringField('door_number', validators=[Optional(strip_whitespace=True), Length(max=16, message="Podany numer lokalu jest za dlugi")])
    city = StringField('city', validators=[DataRequired(), Length(max=32, message="Podana nazwa miejscowosci jest za dluga")])
    zipcode = StringField('zipcode', validators=[DataRequired(), Length(max=16, message="Podany kod pocztowy jest za dlugi")])
    country = StringField('country', validators=[DataRequired(), Length(max=32, message="Podana nazwa kraju jest za dluga")])
    phone = StringField('phone', validators=[DataRequired(), Length(max=16, message="Podany numer telefonu jest za dlugi")])

class OfferForm(Form):
    name = StringField('name', validators=[DataRequired()])
    title = StringField('title', validators=[DataRequired()])
    book_author = StringField('book_author', validators=[DataRequired()])
    price = FloatField('price', validators=[DataRequired()])
    shipping = FloatField('shipping', validators=[DataRequired()])
    count = IntegerField(validators=[DataRequired()])
    body = TextAreaField('body', validators=[DataRequired()])
    category_id = SelectField('category', coerce=int)

class SearchForm(Form):
    search = StringField('search', validators=[DataRequired()])

class NewsletterForm(Form):
    newsletter = StringField('newsletter', validators=[DataRequired(), Email(message="Prosze podac poprawny adres email")])

class PurchaseForm(Form):
    number_of_books = IntegerField('number_of_books', default=1, validators=[DataRequired()])

class PurchaseOverviewForm(Form):
    number_of_books = IntegerField('number_of_books', default=1, validators=[DataRequired()])

class ContactForm(Form):
    name = TextField("name", validators=[DataRequired()])
    email = TextField("email", validators=[DataRequired(), Email(message="Prosze podac poprawny adres email")])
    subject = TextField("subject", validators=[DataRequired()])
    message = TextAreaField("message", validators=[DataRequired()])

class QuestionForm(Form):
    subject = TextField("subject", validators=[DataRequired()])
    message = TextAreaField("message", validators=[DataRequired()])

class CategoryForm(Form):
    name = TextField("name", validators=[DataRequired()])

class CommentForm(Form):
    body = TextAreaField("body", validators=[DataRequired()])
    type = RadioField('type', validators=[DataRequired()], choices=[('true','pozytywny'),('false','negatywny')])

class YourInformationForm(Form):
    user_name = StringField('user_name', validators=[DataRequired(), Length(max=32, message="Podane imie jest za dlugie")])
    surname = StringField('surname', validators=[DataRequired(), Length(max=32, message="Podane nazwisko jest za dlugie")])
    street = StringField('street', validators=[DataRequired(), Length(max=128, message="Podana nazwa ulicy jest za dluga")])
    building_number = StringField('building_number', validators=[DataRequired(), Length(max=16, message="Podany numer budynku jest za dlugi")])
    door_number = StringField('door_number', validators=[Optional(strip_whitespace=True), Length(max=16, message="Podany numer lokalu jest za dlugi")])
    city = StringField('city', validators=[DataRequired(), Length(max=32, message="Podana nazwa miejscowosci jest za dluga")])
    zipcode = StringField('zipcode', validators=[DataRequired(), Length(max=16, message="Podany kod pocztowy jest za dlugi")])
    country = StringField('country', validators=[DataRequired(), Length(max=32, message="Podana nazwa kraju jest za dluga")])
    phone = StringField('phone', validators=[DataRequired(), Length(max=16, message="Podany numer telefonu jest za dlugi")])

class ChangePasswordForm(Form):
    old_password = PasswordField('password', validators=[DataRequired(), Length(min=6, message="Podane haslo jest za krotkie")])
    new_password_1 = PasswordField('password', validators=[DataRequired(), Length(min=6, message="Podane haslo jest za krotkie")])
    new_password_2 = PasswordField('password', validators=[DataRequired(), Length(min=6, message="Podane haslo jest za krotkie"), EqualTo('new_password_2', message="Podane hasla musza byc takie same")])

class AdminOfferEdit(Form):
    offer_id = IntegerField('transaction_id', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    title = StringField('title', validators=[DataRequired()])
    book_author = StringField('book_author', validators=[DataRequired()])
    price = FloatField('price', validators=[DataRequired()])
    shipping = FloatField('shipping', validators=[DataRequired()])
    count = IntegerField('count')
    body = TextAreaField('body', validators=[DataRequired()])
    category_id = SelectField('category', coerce=int)
    timestamp = DateTimeField('timestamp', format='%Y-%m-%d %H:%M:%S.%f', validators=[DataRequired()])
    user_id = IntegerField('user_id', validators=[DataRequired()])
