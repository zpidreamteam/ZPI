from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, RegisterForm
from models import User

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

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
                           
