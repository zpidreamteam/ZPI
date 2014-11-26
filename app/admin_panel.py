from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, admin_permission, views
from datetime import datetime, timedelta
from config import MAX_SEARCH_RESULTS
from models import User, Category, Newsletter, Offer
from forms import CategoryForm

@app.route('/admin')
@app.route('/admin/index')
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
    users = User.query.all()

    return render_template('admin/users.html',
                           title='Zarzadzanie uzytkownikiami',
                           users=users)

@app.route('/admin/categories')
@login_required
@admin_permission.require()
def admin_categories():
    categories = Category.query.all()

    return render_template('admin/categories.html',
                           title='Zarzadzanie kategoriamii',
                           categories=categories)

@app.route('/admin/category/add', methods=['GET', 'POST'])
@login_required
@admin_permission.require()
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(name = form.name.data)

        db.session.add(category)
        db.session.commit()

        flash("Poprawnie dodano kategorie")

        return redirect('admin/categories')

    return render_template('admin/add_category.html',
                            title='Nowa kategoria',
                            form=form)

@app.route('/admin/newsletter')
@login_required
@admin_permission.require()
def admin_newsletters():
    newsletters = Newsletter.query.all()

    return render_template('admin/newsletter.html',
                           title='Zarzadzanie newsletterem',
                           newsletters=newsletters)

@app.route('/admin/offers')
@login_required
@admin_permission.require()
def admin_offers():
    offers = Offer.query.all()

    return render_template('admin/offers.html',
                           title='Zarzadzanie ofertami',
                           offers=offers)

