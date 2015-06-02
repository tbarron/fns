import sys
import pprint
import flask
from app import app, init_db
import os
import pdb
import tempfile

class TestFNS:
    redirect_msg = "You should be redirected automatically to target URL:"

    def test_empty_db_root(self):
        rv = self.app.get('/')
        assert self.redirect_msg in rv.data
        assert '<a href="/login">' in rv.data

    def test_empty_db_login(self):
        rv = self.app.get('/login')
        expected = ['href="static/fns.css"',
                    'name="login" class="fcenter"']
        for exp in expected:
            assert exp in rv.data

    def test_logged_out_profile(self):
        """
        Hitting /profile when logged out should redirect to /login
        """
        self.logged_out_url('/profile')

    def test_logged_out_bookmark(self):
        """
        Hitting /bookmark when logged out should redirect to /login
        """
        self.logged_out_url('/bookmark')

    def test_logged_out_index(self):
        """
        Hitting /index when logged out should redirect to /login
        """
        self.logged_out_url('/index')

    # -------------------------------------------------------------------------
    # Helper methods
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

    # -------------------------------------------------------------------------
    def teardown_method(self, foo):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


def test_sys_path():
    """
    Check that app and flask are imported successfully
    """
    pass

    
