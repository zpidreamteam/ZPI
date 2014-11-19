from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, admin_permission, views
from datetime import datetime, timedelta
from config import MAX_SEARCH_RESULTS

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
@admin_permission.require()
def admin_dashboard():
    user = g.user

    return render_template('admin/index.html',
                           title='Strona glowna',
                           user=user)


@app.route('/admin/users')
@login_required
@admin_permission.require()
def admin_users():
    user = g.user

    return render_template('admin/users.html',
                           title='Zarzadzanie uzytkownikiami',
                           user=user)
