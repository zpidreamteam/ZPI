from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, admin_permission, views, mail
from datetime import datetime, timedelta
from config import MAX_SEARCH_RESULTS
from models import User, Category, Newsletter, Offer, Transaction, Archive_transaction, Archive_user
from forms import CategoryForm, QuestionForm, AdminOfferEdit
from flask.ext.mail import Message
from models import User, Category, Newsletter, Offer, Comment, Archive_offer, Archive_transaction, Transaction
from forms import CategoryForm
from sqlalchemy import create_engine, MetaData
from sqlalchemy import func, exists, and_, or_
from passlib.apps import custom_app_context as pwd_context

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
    users = User.query.filter(or_(User.to_delete==0, User.to_delete==None))

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

@app.route('/admin/newsletter/send', methods=['GET', 'POST'])
@login_required
@admin_permission.require()
def send_newsletter():
    form = QuestionForm()
    if request.method == 'POST':
        recievers = Newsletter.query.order_by(Newsletter.id.desc()).all()
        if form.validate() == False:
            flash('Wymagane wszystkie pola.')
            return render_template('admin/send_newsletter.html', form=form)
        else:
            msg = Message(sender=("no.reply.bookstree@gmail.com"))
            for reciever in recievers:
                msg.add_recipient(reciever.email)
            msg.subject = " %s " % (form.subject.data)
            msg.body = """
            %s
            Aby wypisac sie z tego newslettera wejdz w zakladke pomoc na naszej stronie.
            """ % (form.message.data)
            mail.send(msg)
            print 'Newsletter do %s zostal wyslany' % (msg.recipients)
            flash('Newsletter zostal wyslany.')
        return redirect('/admin/newsletter')
    elif request.method == 'GET':
        print 'ok'
    return render_template('admin/send_newsletter.html',
	                       form=form,
                           title='Wysylanie newslettera')

@app.route('/admin/offers')
@login_required
@admin_permission.require()
def admin_offers():
    offers = Offer.query.filter(or_(Offer.to_delete==0,Offer.to_delete==None))

    return render_template('admin/offers.html',
                           title='Zarzadzanie ofertami',
                           offers=offers)

def delete_transaction(transaction_id, commit):
  transaction = Transaction.query.get(transaction_id)
  if(transaction is None):
    flash('Transakcja nie istnieje! ')
    return False
  if(transaction.is_finalised!=1 or transaction.is_sent!=1):
    flash('Transakcja nie jest zakonczona! Nie mozna jej usunac! ')
    return False

  archive_transaction = Archive_transaction(transaction_id=transaction.id,
                                            timestamp=transaction.timestamp,
                                            user_id=transaction.user_id,
                                            offer_id=transaction.offer_id,
                                            count=transaction.count,
                                            price=transaction.price,
                                            hash_link=transaction.hash_link,
                                            is_finalised=transaction.is_finalised,
                                            is_sent=transaction.is_sent,
                                            is_commented=transaction.is_commented)
  transaction.to_delete = 1
  transaction.timestamp=None
  transaction.user_id=None
  transaction.offer_id=None
  transaction.count=None
  transaction.price=None
  transaction.hash_link=None
  transaction.is_finalised=None
  transaction.is_sent=None
  transaction.is_commented=None

  db.session.add(archive_transaction)
  db.session.add(transaction)
  if commit:
    db.session.commit()
  flash('Transakcja o id: ' + str(transaction.id) + ' zostala usunieta! ')
  return True

def delete_offer(offer_id, commit):
  offer = Offer.query.get(offer_id)
  if(offer is None):
    flash('Oferta nie istnieje! ')
    return False
  if(offer.count!=0):
    flash('Oferta nie jest zakonczona! ')
    return False

  number_of_transactions = db.session.query(func.count(Transaction.id)).\
                               filter_by(offer_id=offer_id).\
                               first()

  transactions = Transaction.query.filter_by(offer_id=offer_id)
  for transaction in transactions:
    if delete_transaction(transaction.id, False)!=True:
      db.session.rollback()
      flash('Transakcja o id:' + str(transaction.id) + ' nie jest zakonczona! ')
      return False

  archive_offer = Archive_offer(offer_id=offer.id,
                                name=offer.name,
                                title=offer.title,
                                book_author=offer.book_author,
                                price=offer.price,
                                shipping=offer.shipping,
                                count=offer.count,
                                body=offer.body,
                                timestamp=offer.timestamp,
                                category_id=offer.category_id,
                                user_id=offer.user_id)
  offer.to_delete = 1
  offer.name=None
  offer.title=None
  offer.book_author=None
  offer.price=None
  offer.shipping=None
  offer.count=None
  offer.body=None
  offer.timestamp=None
  offer.category_id=None
  offer.user_id=None
  db.session.add(archive_offer)
  if commit:
    db.session.commit()

  flash('Oferta o id: ' + str(offer.id) + ' zostala usunieta! ')
  return True

def delete_user(user_id):
  user = User.query.get(user_id)
  if(user is None):
    flash('Uzytkownik nie istnieje! ')
    return redirect(url_for('admin_dashboard'))
  if(user_id==g.user.id):
    flash('Nie mozesz usunac wlasnego konta! ')
    return redirect(url_for('admin_dashboard'))

  offers = db.session.query(func.count(Offer.id)).\
                               filter(Offer.user_id==user_id).\
                               filter(Offer.count!=0).\
                               first()
  if(offers[0]!=0):
    flash('Uzytkownik posiada niezakonczone oferty! ')
    return redirect(url_for('admin_dashboard'))

  transactions = db.session.query(func.count(Transaction.id)).\
                               filter_by(user_id=user_id).\
                               filter(or_(Transaction.is_sent!=1, Transaction.is_finalised!=1)).\
                               first()

  if(transactions[0]!=0):
    flash('Uzytkownik posiada niezakonczone transakcje! ')
    return redirect(url_for('admin_dashboard'))

  transactions = Transaction.query.filter_by(user_id=user_id)
  for transaction in transactions:
    if delete_transaction(transaction.id, False)!=True:
      db.session.rollback()
      flash('Transakcja o id:' + str(transaction.id) + ' nie jest zakonczona! ')
      return redirect(url_for('admin_dashboard'))

  offers = Offer.query.filter_by(user_id=user_id)
  for offer in offers:
    if delete_offer(offer.id, False)!=True:
      db.session.rollback()
      flash('Oferta o id:' + str(offer.id) + ' nie jest zakonczona! ')
      return redirect(url_for('admin_dashboard'))

  archive_user = Archive_user(user_id=user.id,
                                nickname=user.nickname,
                                email=pwd_context.encrypt(user.email),
                                password_hash=user.password_hash,
                                user_name=pwd_context.encrypt(user.user_name),
                                surname=pwd_context.encrypt(user.surname),
                                street=pwd_context.encrypt(user.street),
                                building_number=pwd_context.encrypt(user.building_number),
                                door_number=pwd_context.encrypt(user.door_number),
                                city=user.city,
                                zipcode=user.zipcode,
                                country=user.country,
                                phone=pwd_context.encrypt(user.phone),
                                role_id=user.role_id)
  user.to_delete = 1
  user.nickname=None
  user.email=None
  user.password_hash=None
  user.user_name=None
  user.surname=None
  user.street=None
  user.building_number=None
  user.door_number=None
  user.city=None
  user.zipcode=None
  user.country=None
  user.phone=None
  user.role_id=None
  db.session.add(archive_user)
  db.session.commit()
  flash('Uzytkownik o id: ' + str(user_id) + ' zostal usuniety! ')
  return True

def delete_category(category_id, commit):
  category = Category.query.get(category_id)
  if(category is None):
    flash('Kategoria nie istnieje! ')
    return False

  offers = db.session.query(func.count(Offer.id)).\
                               filter(Offer.category_id==category_id).\
                               filter(or_(Offer.to_delete==0, Offer.to_delete==None)).\
                               filter(Offer.count!=0).\
                               first()

  if int(offers[0])!=0:
    flash('Istnieja niezakonczone oferty dla danej kategorii! ')
    return False

  db.session.delete(category)

  if commit:
    db.session.commit()
  flash('Kategoria o id: ' + str(category_id) + ' zostala usunieta! ')
  return True


def clean_transactions():
  last_transaction = db.session.query(Transaction).order_by(Transaction.id.desc()).first()
  transactions = Transaction.query.filter_by(to_delete=1).filter(Transaction.id!=last_transaction.id)

  for transaction in transactions:
    db.session.delete(transaction)

  db.session.commit()
  return True

def clean_offers():
  last_offer = db.session.query(Offer).order_by(Offer.id.desc()).first()
  offers = Offer.query.filter_by(to_delete=1).filter(Offer.id!=last_offer.id)

  for offer in offers:
    db.session.delete(offer)

  db.session.commit()
  return True

def clean_users():
  last_user = db.session.query(User).order_by(User.id.desc()).first()
  users = User.query.filter_by(to_delete=1).filter(User.id!=last_user.id)

  for user in users:
    db.session.delete(user)

  db.session.commit()
  return True

@app.route('/admin/offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@admin_permission.require()
def admin_offers_edit(offer_id):
  offer = Offer.query.get(offer_id)
  form = AdminOfferEdit()
  categories = [(c.id, c.name) for c in Category.query.all()]
  form.category_id.choices = categories

  if offer is None:
    flash('Brak takiej transakcji!')
    return redirect(url_for('admin_offers'))


  if form.validate_on_submit():
    offer.name = form.name.data
    offer.title = form.title.data
    offer.book_author = form.book_author.data
    offer.price = form.price.data
    offer.shipping = form.shipping.data
    offer.count = form.count.data
    offer.body = form.body.data
    offer.timestamp = form.timestamp.data
    offer.category_id = form.category_id.data
    offer.user_id = form.user_id.data

    db.session.add(offer)
    db.session.commit()

    flash('Zapisano zmiany')
    return redirect(url_for('admin_offers_edit', offer_id=offer_id))

  return render_template('admin/offers_edit.html',
                           title='Zarzadzanie ofertami',
                           offer=offer,
                           form=form,
                           categories=categories)


@app.route('/admin/raports')
@login_required
@admin_permission.require()
def admin_raports():

    return render_template('admin/raports.html',
                           title='Raporty')

@app.route('/admin/comments')
@login_required
@admin_permission.require()
def admin_comments():
    comments = Comment.query.all()

    return render_template('admin/comments.html',
                           title='Komentarze',
                           comments=comments)

@app.route('/admin/offers/delete/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@admin_permission.require()
def admin_offers_delete(offer_id):
    if delete_offer(offer_id, True)==True:
      clean_transactions()
      clean_offers()
      clean_users()
    return redirect(url_for('admin_offers'))

@app.route('/admin/user/delete/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_permission.require()
def admin_user_delete(user_id):
    if delete_user(user_id)==True:
      clean_transactions()
      clean_offers()
      clean_users()
    return redirect(url_for('admin_users'))

@app.route('/admin/transactions')
@login_required
@admin_permission.require()
def admin_transactions():
    transactions = Transaction.query.filter(or_(Transaction.to_delete==0, Transaction.to_delete==None))

    return render_template('admin/transactions.html',
                           title='Komentarze',
                           transactions=transactions)

@app.route('/admin/transactions/delete/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
@admin_permission.require()
def admin_transactions_delete(transaction_id):
    if delete_transaction(transaction_id, True)==True:
      clean_transactions()
    return redirect(url_for('admin_transactions'))

@app.route('/admin/category/delete/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_permission.require()
def admin_category_delete(category_id):
    delete_category(category_id, True)
      
    return redirect(url_for('admin_categories'))