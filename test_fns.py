import sys
import pickle
import pprint
import flask
from flask import redirect, url_for, flash
from app import app, init_db, User, log, g, oid, db
import os
import pdb
import pytest
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
        g.user = User.query.filter_by(name='good').first()
        app.ucache = g.user
        flash(u'Successfully signed in as %s' % g.user.name)
        return redirect('/')


# -----------------------------------------------------------------------------
class TestFNS:
    redirect_msg = "You should be redirected automatically to target URL:"
    login_form = 'name="login"'

    # -------------------------------------------------------------------------
    def test_empty_db_root(self):
        """
        Visiting the root url when not logged in should get the login page
        """
        rv = self.app.get('/')
        assert self.redirect_msg in rv.data
        assert '<a href="/login">' in rv.data

    # -------------------------------------------------------------------------
    def test_empty_db_login(self):
        """
        Visiting the login url should get the login page
        """
        rv = self.app.get('/login')
        expected = ['href="static/fns.css"',
                    'name="login" class="fcenter"']
        for exp in expected:
            assert exp in rv.data

    # -------------------------------------------------------------------------
    def test_logged_in_root(self):
        """
        Hitting / when logged in should redirect to /index
        """
        rv = self.login('http://good.good_domain.org')
        assert "Successfully signed in as good" in rv.data
        assert "Here are your bookmarks" in rv.data
        rv = self.app.get('/')
        assert "Successfully signed in as good" not in rv.data
        assert "Here are your bookmarks" in rv.data
        rv = self.logout()
        assert app.ucache is None
        assert self.login_form in rv.data

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
    def logged_out_url(self, url):
        rv = self.app.get(url)
        assert self.redirect_msg in rv.data
        assert '<a href="/login">' in rv.data

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
    def verify_login_form(self, data):
        explist = ['<link rel="stylesheet" type="text/css" ' +
                   'href="static/fns.css">',
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


def test_sys_path():
    """
    Check that app and flask are imported successfully
    """
    assert 'app' in sys.modules
    assert 'flask' in sys.modules

    
