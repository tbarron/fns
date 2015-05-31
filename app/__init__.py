from flask import Flask, render_template, request, g, session, flash
from flask import redirect, url_for, abort
from flask.ext.openid import OpenID
# from flask.ext.oidc import OpenIDConnect

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

from openid.extensions import pape

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# setup sqlalchemy
Base = declarative_base()
app = Flask(__name__)
app.config.from_object('config')
app.config.update(
    DATABASE_URI = 'sqlite:///flask-openid.db',
    #    SECRET_KEY = 'frabjous_day',
    #    DEBUG = True
)
engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=True,
                                         autoflush=True,
                                         bind=engine))
Base.query = db_session.query_property()

# setup flask-openid
oid = OpenID(app, safe_roots=[], extension_responses=[pape.Response])

# oidc = OpenIDConnect(app, {
#     'OIDC_CLIENT_SECRETS': './client_secrets.json',
#     'SECRET_KEY': 'nobody-knows'
#     })

def start_up(debug=True):
    init_db()
    app.run(debug=debug)

def init_db():
    Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(60))
    email = Column(String(200))
    openid = Column(String(200))

    def __init__(self, name, email, openid):
        self.name = name
        self.email = email
        self.openid = openid

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = User.query.filter_by(openid=session['openid']).first()


@app.after_request
def after_request(response):
    db_session.remove()
    return response


def bm_test_list():
    bml = [
        {
        'bm_name': 'Google',
        'bm_url': 'http://www.google.com',
        'bm_comment': 'my default search engine'
        },
        {
        'bm_name': 'Workflowy',
        'bm_url': 'http://www.workflowy.com',
        'bm_comment': 'my organizer'
        },
        ]
    return bml


@app.route('/')
def index():
    user = {'nickname': 'Thom'}
    # return render_template('index.html', title='Home', user=user)
    return render_template('index.html',
                           title=None,
                           user=user,
                           bm_list=bm_test_list())

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
        flash('Sorry, you need to enter an openid')
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
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))


@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    """If this is the user's first login, the create_or_login function
    will redirect here so that the user can set up his profile.
    """
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            db_session.add(User(name, email, session['openid']))
            db_session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.html', next_url=oid.get_next_url())

@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    """Updates a profile"""
    if g.user is None:
        abort(401)
    form = dict(name=g.user.name, email=g.user.email)
    if request.method == 'POST':
        if 'delete' in request.form:
            db_session.delete(g.user)
            db_session.commit()
            session['openid'] = None
            flash(u'Profile deleted')
            return redirect(url_for('index'))
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
            db_session.commit()
            return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html', form=form)


@app.route('/logout')
def logout():
    if session.pop('openid', None):
        flash(u'You have been signed out')
    else:
        flash(u'You were already signed out')
    login.already_rendered = False
    return redirect(oid.get_next_url())

# app.route('/')(oidc.check(index))

if __name__ == '__main__':
    init_db()
    # app.run()
