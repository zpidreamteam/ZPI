from flask import render_template, flash, redirect
from app import app

@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'MC'}

    return render_template('index.html',
                           title='Home',
                           user=user)