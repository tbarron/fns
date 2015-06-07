from flask import Flask, render_template, request, g, session, flash
from flask import redirect, url_for, abort
from flask.ext.openid import OpenID
# from flask.ext.oidc import OpenIDConnect

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, HiddenField
from wtforms.validators import DataRequired

from openid.extensions import pape

from flask.ext.sqlalchemy import SQLAlchemy
import logging
import logging.handlers
import pdb
import socket

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# setup flask-openid
oid = OpenID(app, safe_roots=[], extension_responses=[pape.Response])

# OpenID Connect is installed in the fns virtualenv, but I have not so far been
# successful in getting it to work
#
# oidc = OpenIDConnect(app, {
#     'OIDC_CLIENT_SECRETS': './client_secrets.json',
#     'SECRET_KEY': 'nobody-knows'
#     })

def start_up(debug=True):
    init_db()
    app.run(debug=debug)

def init_db():
    db.create_all()

def init_logging():
    logger = logging.getLogger("fns")
    logger.setLevel(app.config['LOG_LEVEL'])
    host = socket.gethostname().split('.')[0]
    filepath = app.config['LOG_FILEPATH']
    fh = logging.handlers.RotatingFileHandler(filepath,
                                              maxBytes=1*1024*1024,
                                              backupCount=5)
    strfmt = "%(asctime)s %(filename)s:%(funcName)s %(message)s"
    fmt = logging.Formatter(strfmt, datefmt="%Y.%m%d %H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.info('-' * 35)
    return logger

log = init_logging()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    openid = db.Column(db.String(200))

    def __init__(self, name, email, openid):
        self.name = name
        self.email = email
        self.openid = openid

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer)
    name = db.Column(db.String(80))
    url = db.Column(db.String(250))
    comment = db.Column(db.Text(1024))

    def __init__(self, owner, name, url, comment):
        if type(owner) == int:
            self.owner = owner
        elif type(owner) == str:
            z = User.query.filter_by(name=owner).first()
            self.owner = z.id
        self.name = name
        self.url = url
        self.comment = comment

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class BookmarkForm(Form):
    id = HiddenField('id')
    name = StringField('name')
    url = StringField('url')
    comment = StringField('comment')


@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = User.query.filter_by(openid=session['openid']).first()


@app.after_request
def after_request(response):
    db.session.remove()
    return response


from app import views

# This is for OpenID Connect, which we are not using yet
# app.route('/')(oidc.check(index))
