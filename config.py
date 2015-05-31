import os
dn = os.path.abspath(os.path.dirname(__file__))

WTF_CRSF_ENABLED = True
SECRET_KEY = 'frabjous-day'
DATABASE_URI = 'sqlite:///flask-openid.db'
DEBUG = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(dn, 'fns.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(dn, 'db_repository')
