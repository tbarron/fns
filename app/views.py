from flask import render_template, redirect, request, g, session, flash
from flask import url_for, abort
from openid.extensions import pape
from app import app, oid, LoginForm, BookmarkForm, User, Bookmark, db
from app import log
import fns_util
import pdb
import re
import version


# -----------------------------------------------------------------------------
def logged_in_user():
    if hasattr(g, 'user') and g.user is not None:
        rv = g.user
    elif hasattr(app, 'ucache') and app.ucache is not None:
        rv = app.ucache
    else:
        rv = None
    return rv


# -----------------------------------------------------------------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if logged_in_user() is not None:
        return redirect('/index')
    else:
        return redirect('/login')


# -----------------------------------------------------------------------------
@app.route('/')
@app.route('/index')
def index():
    user = logged_in_user()
    if user is None:
        return redirect('/login')

    return render_template('index.html',
                           title='Float & Sink',
                           user=user,
                           bm_list=fns_util.bm_list(user.id, db),
                           version=version.__version__)


# -----------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    """Does the login via OpenID.  Has to call into `oid.try_login`
    to start the OpenID machinery.
    """
    # if we are already logged in, go back to were we came from
    if logged_in_user() is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if not re.findall('^https*://', openid):
            openid = 'http://' + openid
        if openid:
            pape_req = pape.Request([])
            x = oid.try_login(openid, ask_for=['email', 'nickname'],
                              ask_for_optional=['fullname'],
                              extensions=[pape_req])
            return x
    form = LoginForm()
    if form.validate_on_submit():
        return redirect(oid.get_next_uril())

    msg = oid.fetch_error()
    if msg:
        flash(msg)
    elif fns_util.pu_time():
        flash('Please enter an openid')

    return render_template('login.html',
                           next=oid.get_next_url(),
                           error=oid.fetch_error(),
                           form=form,
                           version=version.__version__)


# -----------------------------------------------------------------------------
@oid.after_login
def create_or_login(resp):
    """This is called when login with OpenID succeeded and it's not
    necessary to figure out if this is the users's first login or not.
    This function has to redirect otherwise the user will be presented
    with a terrible URL which we certainly don't want.
    """
    session['openid'] = resp.identity_url
    if 'pape' in resp.extensions:
        pape_resp = resp.extensions['pape']
        session['auth_time'] = pape_resp.auth_time
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in as %s' % user.name)
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))


# -----------------------------------------------------------------------------
@app.route('/logout')
def logout():
    fns_util.pu_time(reset=True)
    if session.pop('openid', None):
        flash(u'You have been signed out')
    else:
        flash(u'You were already signed out')
    return redirect(oid.get_next_url())


# -----------------------------------------------------------------------------
@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    """If this is the user's first login, the create_or_login function
    will redirect here so that the user can set up his profile.
    """
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            db.session.add(User(name, email, session['openid']))
            db.session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.html',
                           next_url=oid.get_next_url(),
                           version=version.__version__)


# -----------------------------------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    """Updates a profile"""
    if g.user is None:
        return redirect('/login')
    form = dict(name=g.user.name, email=g.user.email)
    if request.method == 'POST':
        if 'delete' in request.form:
            db.session.delete(g.user)
            db.session.commit()
            session['openid'] = None
            flash(u'Profile deleted')
            return redirect(url_for('login'))
        form['name'] = request.form['name']
        form['email'] = request.form['email']
        if not form['name']:
            flash(u'Error: you have to provide a name')
        elif '@' not in form['email']:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            g.user.name = form['name']
            g.user.email = form['email']
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('edit_profile.html',
                           form=form,
                           version=version.__version__)


# -----------------------------------------------------------------------------
@app.route('/bookmark', methods=['GET', 'POST'])
def edit_bookmark():
    """
    Edit a bookmark
    """
    if g.user is None:
        return redirect('/login')
    # pdb.set_trace()
    if request.method == 'POST':
        if 'delete' in request.form:
            bm = Bookmark.query.filter_by(id=request.form['delete']).first()
            db.session.delete(bm)
            db.session.commit()
            return redirect(url_for('index'))
        elif 'edit' in request.form:
            bm = Bookmark.query.filter_by(id= request.form['edit']).first()
            form = BookmarkForm()
            form.id.data = bm.id
            form.name.data = bm.name
            form.url.data = bm.url
            form.comment.data = bm.comment
            return render_template('edit_bookmark.html',
                                   form=form,
                                   bm=bm,
                                   version=version.__version__)
        elif 'id' in request.form and request.form['id']:
            bm = Bookmark.query.filter_by(id=request.form['id']).first()
            if bm is not None:
                bm.name = request.form['name']
                bm.url = fns_util.normalize_url(request.form['url'])
                bm.comment = request.form['comment']
                db.session.commit()
        else:
            url = fns_util.normalize_url(request.form['url'])
            db.session.add(Bookmark(g.user.id,
                                    request.form['name'],
                                    url,
                                    request.form['comment']))
            db.session.commit()
        return redirect(url_for('index'))

    form = BookmarkForm()
    return render_template('edit_bookmark.html',
                           form=form,
                           version=version.__version__)
