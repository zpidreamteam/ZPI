from flask import render_template, flash, redirect, session, url_for, request, g, current_app
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask_principal import ActionNeed, AnonymousIdentity, Identity, identity_changed, identity_loaded, Permission, Principal, UserNeed, RoleNeed
from app import app, db, lm, mail, Storage
from forms import LoginForm, RegisterForm, OfferForm, SearchForm, PurchaseForm, NewsletterForm, PurchaseOverviewForm, YourInformationForm, ChangePasswordForm, ContactForm, QuestionForm, CommentForm
from models import User, Offer, Category, Transaction, Newsletter, Comment
from datetime import datetime, timedelta
from config import MAX_SEARCH_RESULTS, UPLOADS_FOLDER, DEFAULT_FILE_STORAGE, FILE_SYSTEM_STORAGE_FILE_VIEW, UPLOADS_BOOKS_IMAGES
from flask.ext.uploads import save, Upload
from flask.ext.mail import Message
from sqlalchemy.sql.expression import case
from sqlalchemy import func, exists, and_, or_

@app.before_request
def before_request():
    g.user = current_user
    g.search_form = SearchForm()
    g.newsletter_form = NewsletterForm()

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
@app.route('/index')
def index():
    user = g.user

    recently_added = Offer.query.order_by(Offer.timestamp.desc()).limit(4)
    r1 = recently_added[0]
    r2 = recently_added[1]
    r3 = recently_added[2]
    r4 = recently_added[3]

    #TODO sprawdzic poprawnosc po zmianie sposobu filtracji (bez elementow z to_delete==1)
    recently_added = Offer.query.filter(or_(Offer.to_delete==0, Offer.to_delete==None)).order_by(Offer.timestamp.desc()).limit(4)

    return render_template('index.html',
                           title='Strona glowna',
                           user=user,
                           r1=r1,
                           r2=r2,
                           r3=r3,
                           r4=r4)

@app.route('/search', methods=['POST'])
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))

    return redirect(url_for('search_results', query=g.search_form.search.data))

@app.route('/search_results/<query>')
def search_results(query):
    offers = Offer.query.filter(or_(Offer.to_delete==0, Offer.to_delete==None)).whoosh_search(query, MAX_SEARCH_RESULTS).all()
    photos_path = map(lambda offer: UPLOADS_BOOKS_IMAGES + Upload.query.get_or_404(offer.id).name, offers)
    offers_with_photo = zip(offers, photos_path)

    return render_template('search_results.html',
                           query=query,
                           offers_with_photo=offers_with_photo)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data

        user = User.query.filter(or_(User.to_delete==0, User.to_delete==None)).filter_by(email=form.email.data).first()

        if user is None:
            flash('Uzytkownik z mailem {email} nie istnieje.'.format(email=form.email.data))
            return redirect(request.args.get("next") or url_for("index"))

        if user.verify_password(form.password.data) is False:
            flash('Zle haslo.')
            return redirect(request.args.get("next") or url_for("index"))

        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)

        login_user(user, remember=remember_me)

         # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

        return redirect(request.args.get("next") or url_for("index"))

    return render_template('login.html',
                           title='Logowanie',
                           form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return redirect(url_for('index'))

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):

    identity.user = current_user

    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, 'role'):
        print current_user.role
        identity.provides.add(RoleNeed(current_user.role.name))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    nickname=form.nickname.data,
                    user_name=form.user_name.data,
                    surname=form.surname.data,
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

        return redirect(url_for('index'))

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

@app.route('/approve/<int:user_id>/<int:offer_id>/<string:hash_link>/<int:return_payment_code>', methods=['GET'])
def approve(user_id, offer_id, hash_link, return_payment_code):
    t = Transaction.query.filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).filter_by(user_id=user_id, offer_id=offer_id, hash_link=hash_link).first()
    if t is None:
        flash('Podana transakcja nie istnieje!')
        return redirect(url_for('index'))

    ##############################
    ###return_payment_code -> kod zwracany przez zwenetrzna strone przelewow. 200 oznacza udana transakcje
    ##############################

    if return_payment_code==200 and t.is_finalised==0:
        t.is_finalised=1
        db.session.add(t)
        db.session.commit()

        #TO CHECK, zabezpieczenia powinny zapobiec wystapieniu nulla. Jezeli tak sie nie stanie, istnieje ryzyko bledu, gdy mail lub uzytkonik bedzie nullem.
        buyerMail = User.query.get(user_id).email
        sellerMail = User.query.get(Offer.query.get(offer_id).user_id).email

        #Buyer mail
        msg = Message("You've bought a book!",
                  sender="no.reply.bookstree@gmail.com",
                  recipients=["buyerMail"])
        msg.body = "A mail body"
        #mail.send(msg)

        #Seller mail
        msg = Message("You sold a book!",
                  sender="no.reply.bookstree@gmail.com",
                  recipients=["sellerMail"])
        msg.body = "A mail body"
        #mail.send(msg)
    else:
        flash('Transakcja nie przebiegla pomyslnie. Sprobuj ponownie')
        #TODO redirect to error page
        return redirect(url_for('index'))

    return render_template('sold.html')

@login_required
def transaction_validator(user_id, offer_id, count=None):
    offer = Offer.query.get(offer_id)
    error = False

    if offer is None:
        flash('Nie ma takiej oferty.')
        error = True
    elif offer.is_valid() == False:
        flash('Oferta wygasla!')
        error = True
    elif user_id != g.user.id:
        flash('Blad wewnetrzny. Proba Phishingu?')
        error = True
    elif offer.to_delete==1:
        flash('Oferta zostala usunieta! ')
        error = True
    elif count is not None:
        if not offer.is_available(count):
            flash('Nie ma takiej liczby dostepnych egzemplarzy')
            error = True
    return error

@app.route('/purchase/<int:offer_id>', methods=['GET', 'POST'])
@login_required
def purchase(offer_id):
    offer = Offer.query.get(offer_id)
    form = PurchaseForm()

    if transaction_validator(g.user.id, offer_id):
        return redirect(url_for('index'))

    if form.validate_on_submit():
        if transaction_validator(g.user.id, offer_id, form.number_of_books.data):
            return redirect(url_for('index'))

        address = "/purchase/overview/%i/%i/%s" % (g.user.id, offer_id, form.number_of_books.data)

        return redirect(address)

    return render_template('purchase.html',
                           title='Zakup',
                           offer=offer,
                           form=form)

@app.route('/purchase/overview/<int:user_id>/<int:offer_id>/<int:count>', methods=['GET', 'POST'])
@login_required
def purchase_overview(user_id, offer_id, count):

    offer = Offer.query.get(offer_id)
    form = PurchaseOverviewForm()

    if transaction_validator(user_id, offer_id):
        return redirect(url_for('index'))

    total_price = "{:.2f}".format(offer.price * count)

    if form.validate_on_submit():
        if transaction_validator(g.user.id, offer_id, count):
            return redirect(url_for('index'))

        t = Transaction(timestamp=datetime.utcnow(),
                        user_id=g.user.id,
                        offer_id=offer_id,
                        count=form.number_of_books.data,
                        price=(offer.price * count)+offer.shipping,
                        is_finalised=0,
                        is_sent=0,
                        is_commented=0)

        t.hash_link = t.hash_generator()

        alteredOffer = Offer.query.filter_by(id=offer_id).first()
        alteredOffer.count -= form.number_of_books.data

        db.session.add(t)
        db.session.commit()

        address = "/purchase/finalised/%i/%i/%s" % (t.user_id, t.offer_id, t.hash_link)
        return redirect(address)


    return render_template('purchase_overview.html',
                           title='Zakup',
                           form=form, offer_name = offer.name,
                           count=count, total_price=total_price,
                           currency='zl', street=g.user.street,
                           building_number=g.user.building_number,
                           door_number=g.user.door_number,
                           city=g.user.city, zipcode=g.user.zipcode, total_price_plus_shipping=(offer.price * count)+offer.shipping)

@app.route('/purchase/finalised/<int:user_id>/<int:offer_id>/<string:hash_link>', methods=['GET', 'POST'])
@login_required
def purchase_finalised(user_id, offer_id, hash_link):

    t = Transaction.query.filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).filter_by(user_id=user_id, offer_id=offer_id, hash_link=hash_link).first()
    if t is None:
        flash('Podana transakcja nie istnieje!')
        #TODO redirect to 404 error page
        return redirect(url_for('index'))

    payment_method_name = 'przelewy48'

    return render_template('purchase_finalised.html',
                           title='Dokonano zakupu',
                           transaction=t,
                           payment_method_name=payment_method_name)

@app.route('/offer/create', methods=['GET', 'POST'])
@login_required
def create_offer():
    form = OfferForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    categories = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        offer = Offer(name = form.name.data,
		              title = form.title.data,
					  book_author = form.book_author.data,
                      price = form.price.data,
					  shipping = form.shipping.data,
                      count = form.count.data,
                      body = form.body.data,
                      timestamp = datetime.utcnow(),
                      category = Category.query.get(form.category_id.data),
                      author = g.user)

        save(request.files['upload'])

        db.session.add(offer)
        db.session.commit()

        flash("Poprawnie dodano Twoje ogloszenie")

        address = "/offer/read/%i" % (offer.id)
        return redirect(address)

    return render_template('create_offer.html',
                            title='Ogloszenie',
                            form=form,
                            categories=categories)

@app.route('/offer/read/<int:id>')
def read_offer(id):
    offer = Offer.query.get(id)

    #added verification
    if offer is None or offer.to_delete==1:
        flash('Oferta zostala usunieta!')
        return redirect(url_for('index'))

    categories = Category.query.filter().order_by(Category.name.asc()).all()
    user = User.query.filter_by(id=offer.user_id).first()
    photo = Upload.query.get_or_404(id) #TODO need to handle offers without pictures

    photo_path = UPLOADS_BOOKS_IMAGES + photo.name

    comments = Comment.query.filter_by(id_to=user.id)
    if comments is None:
        percentage = 0
        return redirect(url_for('index'))

    poz = 0
    neg = 0
    for c in comments:
        if c.type:
		    poz = poz + 1
        else:
            neg = neg + 1

    tot = poz + neg
    if tot==0:
        percentage=0
    else:
        percentage = poz *100 / tot

    return render_template('read_offer.html',
                            title='Ogloszenie',
                            offer = offer,
                            user=user,
                            poz=poz,
                            neg=neg,
                            tot=tot,
                            percentage=percentage,
                            photo_path = photo_path,
							categories = categories)

@app.route('/offer/<category>')
@app.route('/offer/<category>/<int:page>')
def read_offers_by_category(category, page=1):
    c = Category.query.filter_by(name=category).first()

    #TODO CHECK WHAT HAPPENS WITH DELETED OFFERS
    if c is None:
        flash('Nie ma takiej kategorii %s.' % category)
        return redirect(url_for('index'))

    categories = Category.query.filter().order_by(Category.name.asc()).all()
    offers = c.offers
    photos_path = map(lambda offer: UPLOADS_BOOKS_IMAGES + Upload.query.get_or_404(offer.id).name, offers)
    offers_with_photo = zip(offers, photos_path)

    return render_template('offers.html',
                            title='Ogloszenia',
                            offers_with_photo = offers_with_photo,
							categories = categories)

@app.route('/user/profile/offers/<user_id>')
@app.route('/user/profile/offers/<user_id>/<int:page>')
def read_offers_by_user_id(user_id, page=1):
    c = User.query.filter(or_(User.to_delete==0, User.to_delete==None)).filter_by(id=user_id).first()
    if c is None:
        flash('Nie ma uzytkownika o numerze %s.' % user_id)
        return redirect(url_for('index'))

    categories = Category.query.filter().order_by(Category.name.asc()).all()
    offers = c.offers
    photos_path = map(lambda offer: UPLOADS_BOOKS_IMAGES + Upload.query.get_or_404(offer.id).name, offers)
    offers_with_photo = zip(offers, photos_path)

    return render_template('offers.html',
                            title='Ogloszenia',
                            offers_with_photo = offers_with_photo,
							categories = categories)

@app.route('/offers')
@app.route('/offers/<int:page>')
def read_offers(page=1):
    offers = Offer.query.filter(or_(Offer.to_delete==0, Offer.to_delete==None)).order_by(Offer.timestamp.desc()).all()
    categories = Category.query.filter().order_by(Category.name.asc()).all()
    photos_path = map(lambda offer: UPLOADS_BOOKS_IMAGES + Upload.query.get_or_404(offer.id).name, offers)
    offers_with_photo = zip(offers, photos_path)

    return render_template('offers.html',
                            title='Ogloszenia',
                            offers_with_photo = offers_with_photo,
							categories = categories)

@app.route('/przelewy48/<int:user_id>/<int:offer_id>/<string:hash_link>')
def przelewy48(user_id, offer_id, hash_link):
    approve_method_name='approve'

    return render_template('przelewy48.html',
                           approve_method_name=approve_method_name,
                           user_id=user_id,
                           offer_id=offer_id,
                           hash_link=hash_link)

@app.route('/add_to_newsletter', methods=['GET', 'POST'])
def add_to_newsletter():
    if not g.newsletter_form.validate_on_submit():
        flash("Jesli chcesz zapisac sie do newslettera musisz podac swojego prawidlowego maila")
        return redirect(url_for('index'))

    return redirect(url_for('add_to_newsletter_confirm', email=g.newsletter_form.newsletter.data))

@app.route('/add_to_newsletter_confirm/<email>')
def add_to_newsletter_confirm(email):
    newsletter = Newsletter(email = email)

    db.session.add(newsletter)
    db.session.commit()

    flash("Zostales zapisany do newslettera")

    return redirect(url_for('index'))

@app.route('/delete_from_newsletter', methods=['GET', 'POST'])
def delete_from_newsletter():
    form = NewsletterForm()
    if form.validate_on_submit():
        return redirect(url_for('delete_from_newsletter_confirm', email=form.newsletter.data))

    flash("Aby wypisac sie z newslettera musisz podac swojego prawidlowego maila")
    return render_template('delete_from_newsletter.html',
                           title='Usun z newslettera',
                           form=form)

@app.route('/help')
def faq():
    return render_template('help.html',
                           title='Pomoc')

@app.route('/delete_from_newsletter_confirm/<email>')
def delete_from_newsletter_confirm(email):
    Newsletter.query.filter_by(email=email).delete()

    db.session.commit()

    flash("Zostales wypisany z newslettera")

    return redirect(url_for('index'))

@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('Wymagane wszystkie pola.')
            return render_template('contact_us.html', form=form)
        else:
            msg = Message(form.subject.data, sender=("Formularz kontaktowy bookstree", form.email.data), recipients=['contact.bookstree@gmail.com'])
            msg.body = """
            %s <%s> napisal:
            %s
            """ % (form.name.data, form.email.data, form.message.data)
            mail.send(msg)
            flash('Wiadomosc zostala wyslana.')
            return redirect(url_for('index'))

    elif request.method == 'GET':
        return render_template('contact_us.html', form=form)

@app.route('/question/<int:offer_id>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def question(user_id,offer_id):
    form = QuestionForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('Wymagane wszystkie pola.')
            return render_template('question.html', form=form)
        else:
            reciever = User.query.get(user_id)
            my_offer = Offer.query.get(offer_id)
            msg = Message(sender=("Formularz kontaktowy bookstree", g.user.email), recipients=[reciever.email])
            msg.subject = "%s Oferta %s o numerze ID: %s " % (form.subject.data, my_offer.name, my_offer.id)
            msg.body = """
            %s <%s> napisal:
            %s
            """ % (g.user.nickname, g.user.email, form.message.data)
            mail.send(msg)

            flash('Wiadomosc zostala wyslana.')

            address = "/offer/read/%i" % (offer_id)
            return redirect(address)

    elif request.method == 'GET':
        return render_template('question.html', form=form)

@app.route('/user/profile/<int:user_id>')
@login_required
def show_profile(user_id):
    comments = Comment.query.filter_by(id_to=user_id)
    if comments is None:
        flash('Uzytkownik nie ma komentarzy.')
        return redirect(url_for('index'))

    #added veryfication
    user = User.query.filter(or_(User.to_delete==0, User.to_delete==None)).filter_by(id=user_id).first()
    if user is None:
        flash('Uzytkownik nie istnieje lub usunal konto!')
        return redirect(url_for('index'))

    poz = 0
    neg = 0
    for c in comments:
        if c.type:
		    poz = poz + 1
        else:
            neg = neg + 1

    tot = poz + neg
    if tot==0:
        percentage=0
    else:
        percentage = poz *100 / tot
    return render_template('profile.html',
                            title='Profil',
							user=user,
							poz=poz,
							neg=neg,
							tot=tot,
                            percentage=percentage,
							user_id=user_id)

@app.route('/user/profile/comments/<int:user_id>')
@login_required
def show_comments(user_id):
    user = User.query.filter(or_(User.to_delete==0, User.to_delete==None)).filter_by(id=user_id).first()
    if user is None:
        flash('Uzytkownik nie istnieje lub usunal konto!')
        return redirect(url_for('index'))

    comments = Comment.query.filter_by(id_to=user_id)
    if comments is None:
        flash('Uzytkownik nie ma komentarzy.')
        return redirect(url_for('index'))

    return render_template('comments.html',
                            title='Komentarze',
                            comments=comments)

@app.route('/comment/new/<int:trans_id>/', methods=['GET', 'POST'])
@login_required
def new_comment(trans_id):
    form = CommentForm()
    transactions = db.session.query(Transaction.id, Transaction.offer_id, Offer.user_id).\
                               filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                               filter_by(id=trans_id, user_id=g.user.id, is_finalised=1, is_sent=1, is_commented=0).\
                               join(Offer, Offer.id==Transaction.offer_id).first()

    if transactions is None:
        flash('Nie mozesz dodac takiego komentarza!')
        return redirect(url_for('index'))

    if form.validate_on_submit():

        is_positive = 1 if form.type.data=='true' else 0
        comment = Comment(timestamp = datetime.utcnow(),
                      id_from = g.user.id,
                      id_to = transactions.user_id,
                      transaction_id = trans_id,
                      type = is_positive,
                      body = form.body.data)

        db.session.add(comment)

        alter_transaction = Transaction.query.get(trans_id)
        alter_transaction.is_commented = 1
        db.session.add(alter_transaction)

        db.session.commit()
        #TODO przekierowanie do odpowiedniej storny
        flash("Poprawnie dodano Twoj komentarz")
        return redirect(url_for('user_dashboard_to_wait'))

    return render_template('new_comment.html',
                            title='Comment',
                            form=form)
#User Dashboard
@login_required
@app.route('/user/dashboard/')
def user_dashboard():
    #added veryfication
    number_of_transactions_to_pay_for = db.session.query(func.count(Transaction.id)).\
                               filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                               filter_by(user_id=g.user.id, is_finalised=0).\
                               first()
    #added veryfication
    q = db.session.query(Offer.id, func.count(Transaction.id)).\
                              filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                              filter(or_(Offer.to_delete==0, Offer.to_delete==None)).\
                              filter_by(user_id=g.user.id).\
                              join(Transaction, Transaction.offer_id==Offer.id).\
                              filter_by(is_finalised=1, is_sent=0).\
                              join(User, User.id==Transaction.user_id)

    number_of_transactions_to_wait = db.session.query(func.count(Transaction.id)).\
                               filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                               filter_by(user_id=g.user.id, is_finalised=1, is_sent=0).\
                               first()

    #added veryfication
    transactions_to_comment = db.session.query(Transaction.id, func.count(Transaction.id), Transaction.timestamp,
                                               Transaction.offer_id, Offer.name, Offer.user_id).\
                               filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                               filter_by(user_id=g.user.id, is_finalised=1, is_sent=1, is_commented=0).\
                               join(Offer, Offer.id==Transaction.offer_id).\
                               order_by(Transaction.timestamp.desc())

    return render_template('user_dashboard.html', number_of_transactions_to_pay_for=number_of_transactions_to_pay_for,
                           number_of_transactions_to_send=q, transactions_to_comment=transactions_to_comment,
                           number_of_transactions_to_wait=number_of_transactions_to_wait)

@login_required
@app.route('/user/dashboard/to/pay')
def user_dashboard_to_pay():
    #added veryfication
    transactions = db.session.query(Transaction.id, Transaction.user_id,
                                    Transaction.offer_id, Offer.name, Transaction.timestamp,
                                    Transaction.count, Transaction.price,
                                    Transaction.hash_link).\
                               filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                               filter_by(user_id=g.user.id, is_finalised=0).\
                               join(Offer, Offer.id==Transaction.offer_id).\
                               order_by(Transaction.timestamp.desc())

    return render_template('user_dashboard_to_pay.html', transactions=transactions)

@login_required
@app.route('/user/dashboard/to/wait')
def user_dashboard_to_wait():
    #added veryfication
    transactions = db.session.query(Transaction.id, Transaction.user_id,
                                    Transaction.offer_id, Offer.name, Transaction.timestamp,
                                    Transaction.count, Transaction.price,
                                    Transaction.hash_link, Transaction.is_sent, Transaction.is_commented).\
                               filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                               filter_by(user_id=g.user.id, is_finalised=1, is_commented=0).\
                               join(Offer, Offer.id==Transaction.offer_id).\
                               order_by(Transaction.timestamp.desc())

    return render_template('user_dashboard_to_wait.html', transactions=transactions)

@login_required
@app.route('/user/dashboard/to/send')
def user_dashboard_to_send():
    #added veryfication
    transactions = db.session.query(Offer.id, Offer.name, Offer.price, Transaction.id.label("transact_id"),
                                    Transaction.user_id, User.street, Transaction.timestamp,
                                    User.building_number, User.door_number,
                                    User.city, User.zipcode).\
                              filter(or_(Offer.to_delete==0, Offer.to_delete==None)).\
                              filter_by(user_id=g.user.id).\
                              join(Transaction, Transaction.offer_id==Offer.id).\
                              filter_by(is_finalised=1, is_sent=0).\
                              join(User, User.id==Transaction.user_id)

    return render_template('user_dashboard_to_send.html', transactions=transactions)

@login_required
@app.route('/user/dashboard/to/send/check/<int:transaction_id>', methods=['GET', 'POST'])
def user_dashboard_to_send_check(transaction_id):
    #added veryfication
    t = db.session.query(Offer.user_id, Transaction.id).\
                              filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                              filter(or_(Offer.to_delete==0, Offer.to_delete==None)).\
                              filter_by(user_id=g.user.id).\
                              join(Transaction, Transaction.offer_id==Offer.id).\
                              filter_by(is_finalised=1, is_sent=0, id=transaction_id).\
                              join(User, User.id==Transaction.user_id).first()
    if t is None:
        flash('Nie ma takiej transakcji!')
    else:
        transaction = Transaction.query.filter_by(id=transaction_id).first()
        transaction.is_sent = 1
        db.session.add(transaction)
        db.session.commit()
        flash('Potwierdzono wyslanie zamowienia')

    return redirect(url_for('user_dashboard_to_send'))

@login_required
@app.route('/user/dashboard/my/offers/current')
def user_dashboard_my_offers_current():
    #added veryfication
    offers = db.session.query(Offer.id, Offer.name, Offer.timestamp,
                              Offer.price, Offer.count).\
                              filter(or_(Offer.to_delete==0, Offer.to_delete==None)).\
                              filter_by(user_id=g.user.id).\
                              filter(Offer.count!=0).\
                              order_by(Offer.timestamp.desc())

    return render_template('user_dashboard_my_offers_current.html', offers=offers)

@login_required
@app.route('/user/dashboard/my/offers/close/<int:offer_id>', methods=['GET', 'POST'])
def offer_close(offer_id):
    #added veryfication
    offer = Offer.query.filter(or_(Offer.to_delete==0, Offer.to_delete==None)).filter_by(id=offer_id, user_id=g.user.id).first()

    if offer is None:
        flash('Nie ma takiej oferty')
    elif offer.count == 0:
        flash('Oferta jest juz zamknieta!')
    else:
        offer.count = 0
        db.session.add(offer)
        db.session.commit()
        flash('Zamknieto oferte')

    return redirect(url_for('user_dashboard_my_offers_current'))

@login_required
@app.route('/user/dashboard/about/me/', methods=['GET', 'POST'])
def about_me():
    user = User.query.get(g.user.id)
    form = YourInformationForm()
    if form.validate_on_submit():
        user.user_name = form.user_name.data
        user.surname = form.surname.data
        user.street = form.street.data
        user.building_number = form.building_number.data
        user.door_number = form.door_number.data
        user.city = form.city.data
        user.zipcode = form.zipcode.data
        user.country = form.country.data
        user.phone = form.phone.data

        db.session.add(user)
        db.session.commit()

        flash("Dane zmieniono!")

        return redirect(url_for('about_me'))

    return render_template('user_dashboard_about_me.html', form=form, user=user)

@login_required
@app.route('/user/dashboard/archive/')
def archive():
    #added veryfication
    transactions_bought = db.session.query(Transaction.id, Transaction.user_id, Offer.name,
                                    Transaction.offer_id, Offer.name, Transaction.timestamp,
                                    Transaction.count, Transaction.price,
                                    Transaction.hash_link, User.nickname).\
                               filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                               filter_by(user_id=g.user.id, is_finalised=1, is_sent=1).\
                               join(Offer, Offer.id==Transaction.offer_id).\
                               join(User, User.id==Offer.user_id).\
                               order_by(Transaction.timestamp.desc())
    #added veryfication
    transactions_sold = db.session.query(Offer.id, Offer.name, Transaction.id.label("transact_id"),
                                    Transaction.user_id, Transaction.count, Transaction.price, User.street, Transaction.timestamp,
                                    User.building_number, User.door_number,
                                    User.city, User.zipcode, User.nickname).\
                              filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                              filter_by(user_id=g.user.id).\
                              join(Transaction, Transaction.offer_id==Offer.id).\
                              filter_by(is_finalised=1, is_sent=1).\
                              join(User, User.id==Transaction.user_id).\
                              order_by(Transaction.timestamp.desc())

    return render_template('user_dashboard_archive.html', transactions_bought=transactions_bought,
                           transactions_sold=transactions_sold)

@login_required
@app.route('/user/dashboard/change/password/', methods=['GET', 'POST'])
def change_password():
    user = User.query.get(g.user.id)

    form = ChangePasswordForm()
    if form.validate_on_submit():
        if user.verify_password(form.old_password.data):
            user.hash_password(form.new_password_1.data)
            db.session.add(user)
            db.session.commit()
            flash("Haslo zostalo zmienione!")
        else:
            flash("Obecne haslo nie jest poprawne")
    return render_template('user_dashboard_change_password.html', form=form)

@login_required
@app.route('/user/dashboard/comment/', methods=['GET', 'POST'])
def comment():

    transactions_to_comment = db.session.query(Transaction.id, Transaction.timestamp,
                                               Transaction.offer_id, Offer.name, Offer.user_id).\
                               filter(or_(Transaction.to_delete==0, Transaction.to_delete==None)).\
                               filter_by(user_id=g.user.id, is_finalised=1, is_sent=1, is_commented=0).\
                               join(Offer, Offer.id==Transaction.offer_id).\
                               order_by(Transaction.timestamp.desc())


    return render_template('user_dashboard_comment.html', transactions_to_comment=transactions_to_comment)
