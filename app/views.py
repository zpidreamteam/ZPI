from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, mail, Storage
from forms import LoginForm, RegisterForm, OfferForm, SearchForm, PurchaseForm, NewsletterForm, PurchaseOverviewForm
from models import User, Offer, Category, Transaction, Newsletter
from datetime import datetime, timedelta
from config import MAX_SEARCH_RESULTS, UPLOADS_FOLDER, DEFAULT_FILE_STORAGE, FILE_SYSTEM_STORAGE_FILE_VIEW, UPLOADS_BOOKS_IMAGES
from flask.ext.uploads import save, Upload
from flask.ext.mail import Message

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

    return render_template('index.html',
                           title='Strona glowna',
                           user=user)

@app.route('/search', methods=['POST'])
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))

    return redirect(url_for('search_results', query=g.search_form.search.data))

@app.route('/search_results/<query>')
def search_results(query):
    results = Offer.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()

    return render_template('search_results.html',
                           query=query,
                           results=results)

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
            return redirect(request.args.get("next") or url_for("index"))

        if user.verify_password(form.password.data) is False:
            flash('Wrong password')
            return redirect(request.args.get("next") or url_for("index"))

        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(user, remember=remember_me)

        return redirect(request.args.get("next") or url_for("index"))
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
    t = Transaction.query.filter_by(user_id=user_id, offer_id=offer_id, hash_link=hash_link).first()
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
                        price=offer.price,
                        is_finalised=0)

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
                           city=g.user.city, zipcode=g.user.zipcode)

@app.route('/purchase/finalised/<int:user_id>/<int:offer_id>/<string:hash_link>', methods=['GET', 'POST'])
@login_required
def purchase_finalised(user_id, offer_id, hash_link):

    t = Transaction.query.filter_by(user_id=user_id, offer_id=offer_id, hash_link=hash_link).first()
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
                            form=form)

@app.route('/offer/read/<int:id>')
def read_offer(id):
    offer = Offer.query.get(id)
    photo = Upload.query.get_or_404(id) #TODO need to handle offers without pictures

    photo_path = UPLOADS_BOOKS_IMAGES + photo.name

    return render_template('read_offer.html',
                            title='Ogloszenie',
                            offer = offer,
                            photo_path = photo_path)

@app.route('/offer/<category>')
@app.route('/offer/<category>/<int:page>')
def read_offers_by_category(category, page=1):
    c = Category.query.filter_by(name=category).first()
    if c is None:
        flash('Nie ma takiej kategorii %s.' % category)
        return redirect(url_for('index'))

    offers = c.offers

    return render_template('offers.html',
                            title='Ogloszenia',
                            offers = offers)

@app.route('/offers')
@app.route('/offers/<int:page>')
def read_offers(page=1):
    offers = Offer.query.order_by(Offer.timestamp.desc()).all()

    return render_template('offers.html',
                            title='Ogloszenia',
                            offers = offers)

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
