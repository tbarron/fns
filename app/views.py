from flask import render_template, redirect, request, g, session, flash
from flask import url_for, abort
from openid.extensions import pape
from app import app, oid, LoginForm, User, db
import fns_util


# -----------------------------------------------------------------------------
@app.route('/')
@app.route('/index')
def index():
    user = None
    try:
        user = g.user
    except NameError:
        pass

    if user is None:
        return redirect('/login')

    return render_template('index.html',
                           title='Float & Sink',
                           user=user,
                           bm_list=fns_util.bm_test_list())


# -----------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    """Does the login via OpenID.  Has to call into `oid.try_login`
    to start the OpenID machinery.
    """
    # if we are already logged in, go back to were we came from
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            pape_req = pape.Request([])
            return oid.try_login(openid, ask_for=['email', 'nickname'],
                                         ask_for_optional=['fullname'],
                                         extensions=[pape_req])
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
                           form=form)


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
    return render_template('create_profile.html', next_url=oid.get_next_url())


# -----------------------------------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    """Updates a profile"""
    if g.user is None:
        abort(401)
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
    return render_template('edit_profile.html', form=form)
