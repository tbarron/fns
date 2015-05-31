from flask import render_template
from app import app
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
        if g.user is None:
            return redirect('/login')
    except NameError:
        pass

    return render_template('index.html',
                           title='Float & Sink',
                           user=user,
                           bm_list=fns_util.bm_test_list())

