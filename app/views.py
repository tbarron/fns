from flask import render_template, redirect, request, g, session, flash
from openid.extensions import pape
from app import app, oid, LoginForm, User
import fns_util

# @app.route('/')
# @app.route('/index')
# def index():
#     return "Hello, world!"

@app.route('/')
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
        flash('Login requested for OpenID="%s", remember_me=%s' %
              (form.openid.data, str(form.remember_me.data)))
        return redirect(oid.get_next_uril())

    msg = oid.fetch_error()
    if msg:
        flash(msg)
    if hasattr(login, 'already_rendered') and login.already_rendered:
        flash('Please enter an openid')
    else:
        login.already_rendered = True
    return render_template('login.html',
                           next=oid.get_next_url(),
                           error=oid.fetch_error(),
                           form=form)


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


@app.route('/logout')
def logout():
    if session.pop('openid', None):
        flash(u'You have been signed out')
    else:
        flash(u'You were already signed out')
    login.already_rendered = False
    return redirect(oid.get_next_url())

