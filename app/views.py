from flask import render_template, flash, redirect
from app import app
from .forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'MC'}

    return render_template('index.html',
                           title='Strona glowna',
                           user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Mail="%s", remember_me=%s' %
              (form.mail.data, str(form.remember_me.data)))
        return redirect('/index')

    return render_template('login.html',
                           title='Logowanie',
                           form=form)