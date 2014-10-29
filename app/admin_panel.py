from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, admin_permission
from datetime import datetime, timedelta
from config import MAX_SEARCH_RESULTS

@app.route('/admin/dashboard')
@login_required
@admin_permission.require()
def admin_dashboard():

    return "admin_dashboard"