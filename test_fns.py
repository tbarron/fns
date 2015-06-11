import sys
import pickle
import pprint
import flask
from flask import redirect, url_for, flash
from app import app, init_db, User, log, g, oid, db
import os
import pdb
import pytest
import re
import tempfile
from contextlib import contextmanager
from flask import appcontext_pushed


# -----------------------------------------------------------------------------
def contents(fpath):
    with open(fpath, 'r') as f:
        rv = f.read()
    return rv


# -----------------------------------------------------------------------------
@contextmanager
def user_set(app, user):
    def handler(sender, **kwargs):
        g.user = user
    with appcontext_pushed.connected_to(handler, app):
        yield


# -----------------------------------------------------------------------------
class LoginTestMonkeyPatch(object):
    # -------------------------------------------------------------------------
    def __init__(self, oid=None, default_response=None):
        if default_response is None:
            self.data = contents('rsp.data')
        else:
            self.data = default_response
        if oid is not None:
            self.oid = oid
            self.oid.try_login = self.try_login

    # -------------------------------------------------------------------------
    def try_login(self, *args, **kwargs):
        openid = re.sub('^https://', 'http://', args[0])
        if not re.findall('^http://', openid):
            r = flask.Response()
            r.data = open('malformed.openid.rsp').read()
            return r
        g.user = User.query.filter_by(openid=openid).first()
        app.ucache = g.user
        if g.user is not None:
            flash(u'Successfully signed in as %s' % g.user.name)
            return redirect('/')
        else:
            return redirect('/login')

# -----------------------------------------------------------------------------
class TestFNS:
    redirect_msg = "You should be redirected automatically to target URL:"
    login_form = 'name="login"'

    # -------------------------------------------------------------------------
    def test_login_noscheme(self):
        """
        Logging in with no scheme -- app should add scheme for us
        """
        self.log_inout('good.good_domain.org')

    # -------------------------------------------------------------------------
    def test_login_https(self):
        """
        Logging in with no scheme -- app should add scheme for us
        """
        self.log_inout('https://good.good_domain.org')

    # -------------------------------------------------------------------------
    def test_logged_in_root(self):
        """
        Hitting / when logged in should redirect to /index
        """
        self.log_inout('http://good.good_domain.org', '/')

    # -------------------------------------------------------------------------
    def test_logged_in_unsupported(self):
        """
        Hitting an unsupported url when logged in should redirect to /index
        """
        self.log_inout('http://good.good_domain.org',
                       '/unsupported',
                       follow_redirects=True)

    # -------------------------------------------------------------------------
    def test_logged_out_root(self):
        """
        Hitting / when logged out should redirect to /login
        """
        self.logged_out_url('/')

    # -------------------------------------------------------------------------
    def test_logged_out_profile(self):
        """
        Hitting /profile when logged out should redirect to /login
        """
        self.logged_out_url('/profile')

    # -------------------------------------------------------------------------
    def test_logged_out_login(self):
        """
        Hitting /login when logged out should return the login page
        """
        rv = self.app.get('/login')
        self.verify_login_form(rv.data)

    # -------------------------------------------------------------------------
    def test_logged_out_bookmark(self):
        """
        Hitting /bookmark when logged out should redirect to /login
        """
        self.logged_out_url('/bookmark')

    # -------------------------------------------------------------------------
    def test_logged_out_index(self):
        """
        Hitting /index when logged out should redirect to /login
        """
        self.logged_out_url('/index')

    # -------------------------------------------------------------------------
    def test_logged_out_unsupported(self):
        """
        Hitting /index when logged out should redirect to /login
        """
        self.logged_out_url('/unsupported')

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------
    def login(self, openid):
        LoginTestMonkeyPatch(oid)
        rv = self.app.post('/login',
                           data=dict(openid=openid),
                           follow_redirects=True)
        return rv

    # -------------------------------------------------------------------------
    def logout(self):
        app.ucache = None
        return self.app.get('/logout', follow_redirects=True)

    # -------------------------------------------------------------------------
    def log_inout(self, openid, url='/', follow_redirects=False):
        rv = self.login(openid)
        self.verify_index_form(rv.data,
                               present="Successfully signed in as good")
        rv = self.app.get(url, follow_redirects=follow_redirects)
        self.verify_index_form(rv.data,
                               absent="Successfully signed in as good")
        rv = self.logout()
        self.verify_logged_out()
        self.verify_login_form(rv.data)

    # -------------------------------------------------------------------------
    def logged_out_url(self, url):
        rv = self.app.get(url)
        self.verify_redirect_to('login', rv.data)

    # -------------------------------------------------------------------------
    def setup_method(self, foo):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        self.app = app.test_client()
        init_db()
        u = User('good',
                 'valid_email@good_domain.org',
                 'http://good.good_domain.org')
        db.session.add(u)

    # -------------------------------------------------------------------------
    def teardown_method(self, foo):
        pass
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    # -------------------------------------------------------------------------
    def verify_logged_out(self):
        assert app.ucache is None

    # -------------------------------------------------------------------------
    def verify_login_form(self, data):
        explist = ['<link rel="stylesheet" type="text/css" ' +
                   'href="static/fns.css">',
                   '<p> OpenID:',
                   '<input autofocus="autofocus" id="openid" ' +
                   'name="openid" size="80" type="text" value="">',
                   'autofocus',
                   'class="fcenter"']
        for exp in explist:
            assert exp in data

    # -------------------------------------------------------------------------
    def verify_index_form(self, data, present=None, absent=None):
        explist = ['<link rel="stylesheet" type="text/css" ' +
                   'href="static/fns.css">',
                   '<h3>Hello, good</h3>',
                   'Here are your bookmarks']
        if present:
            if type(present) == str:
                explist.append(present)
            elif type(present) == list:
                explist.extend(present)
        for exp in explist:
            assert exp in data
        if absent:
            if type(absent) == str:
                assert absent not in data
            elif type(absent) == list:
                for item in absent:
                    assert item not in data


    # -------------------------------------------------------------------------
    def verify_redirect_to(self, target=None, data=None):
        assert self.redirect_msg in data
        if target:
            assert '<a href="/%s">' % target in data


# -----------------------------------------------------------------------------
def test_sys_path():
    """
    Check that app and flask are imported successfully
    """
    assert 'app' in sys.modules
    assert 'flask' in sys.modules

    
