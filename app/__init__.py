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


from app import views

# app.route('/')(oidc.check(index))

if __name__ == '__main__':
    init_db()
    # app.run()
