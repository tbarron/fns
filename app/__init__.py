from flask import Flask, render_template, request, g, session, flash
from flask import redirect, url_for, abort
from flask.ext.openid import OpenID
# from flask.ext.oidc import OpenIDConnect

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

from openid.extensions import pape

from flask.ext.sqlalchemy import SQLAlchemy

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
    bm_name = db.Column(db.String(80))
    bm_url = db.Column(db.String(250))
    bm_comment = db.Column(db.Text(1024))

    def __init__(self, owner, name, url, comment):
        if type(owner) == int:
            self.owner = owner
        elif type(owner) == str:
            z = User.query.filter_by(name=owner).first()
            self.owner = z.id
        self.bm_name = name
        self.bm_url = url
        self.bm_comment = comment

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
    db.session.remove()
    return response


from app import views

# This is for OpenID Connect, which we are not using yet
# app.route('/')(oidc.check(index))
