from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, RegisterForm, OfferForm
from models import User, Offer, Category
from datetime import datetime, timedelta

@app.before_request
def before_request():
    g.user = current_user

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user

    return render_template('index.html',
                           title='Strona glowna',
                           user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data

        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('User with email {email} not found.'.format(email=form.email.data))
            return redirect(url_for('index'))

        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(user, remember=remember_me)

        return redirect('/index')

    return render_template('login.html',
                           title='Logowanie',
                           form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    nickname=form.nickname.data,
                    street=form.street.data,
                    building_number=form.building_number.data,
                    door_number=form.door_number.data,
                    city=form.city.data,
                    zipcode=form.zipcode.data,
                    country=form.country.data,
                    phone=form.phone.data)
        user.hash_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect('/index')

    return render_template('register.html',
                           title='Rejestracja',
                           form=form)

@app.route('/offer/create', methods=['GET', 'POST'])
@login_required
def create_offer():
    form = OfferForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        offer = Offer(name = form.name.data,
                      price = form.price.data,
                      count = form.count.data,
                      body = form.body.data,
                      timestamp = datetime.utcnow(),
                      category = Category.query.get(form.category_id.data),
                      author = g.user)
        db.session.add(offer)
        db.session.commit()
        flash("Poprawnie dodano Twoje ogloszenie")
        return redirect('/index')

    return render_template('create_offer.html',
                            title='Ogloszenie',
                            form=form)

@app.route('/offer/read/<int:id>')
def read_offer(id):
    offer = Offer.query.get(id)

    return render_template('read_offer.html',
                            title='Ogloszenie',
                            offer = offer)

@app.route('/offer/<category>')
@app.route('/offer/<category>/<int:page>')
def read_offers_by_category(category, page=1):
    c = Category.query.filter_by(name=category).first()
    if c is None:
        flash('Category %s not found.' % category)
        redirect(url_for('index'))

    offers = c.offers

    return render_template('offers.html',
                            title='Ogloszenia',
                            offers = offers)

