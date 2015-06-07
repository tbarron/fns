#!/usr/bin/env python
import bscr
import sys
from app import start_up
import pdb

# -----------------------------------------------------------------------------
def main(args=None):
    if args is None:
        args = sys.argv
    bscr.util.dispatch(__name__, 'fns', args)

# -----------------------------------------------------------------------------
def fns_hello(args):
    """hello - verify that this is working
    """
    print("hello. This is fns.")


# -----------------------------------------------------------------------------
def fns_genrsp(args):
    """genrsp - write out the response to a logged in get
    """
    f = open('rsp.data.new', 'w')
    f.write("""
<!DOCTYPE html>
<html><head>
  <link rel="stylesheet" type="text/css" href="static/fns.css">

  <title>

    Index: Float &amp; Sink

</title>

</head><body>
  <table><tr>
    <td>| <a href="index">Home</a>
    <td>| <a href="lists">Lists</a>
    <td>| <a href="profile">Profile</a>
    <td>| <a href="logout">Logout</a> |
  </tr></table>





    <h2>Index: Float &amp; Sink</h2>


  <h3>Hello, newbie</h3>

  <h4>Here are your bookmarks:</h4>

  <form action="bookmark" method="post">
  <table class="bm_list">

    <tr><div>
        <td><p><a href="http://www.google.com">google</a>
            <br>number one search engine</p>
        <td><button type=submit name="delete" value="1">Delete</button>
        <td><button type=submit name="edit" value="1">Edit</button>
    </div></tr>

    <tr><div>
        <td><p><a href="https://gmail.com">gmail</a>
            <br>online mail client</p>
        <td><button type=submit name="delete" value="2">Delete</button>
        <td><button type=submit name="edit" value="2">Edit</button>
    </div></tr>

    <tr><div>
        <td><p><a href="http://www.ornl.gov">ORNL</a>
            <br>where I work</p>
        <td><button type=submit name="delete" value="4">Delete</button>
        <td><button type=submit name="edit" value="4">Edit</button>
    </div></tr>

    <tr><div>
        <td><p><a href="https://example.com">new bookmark</a>
            <br>yet another bookmark</p>
        <td><button type=submit name="delete" value="5">Delete</button>
        <td><button type=submit name="edit" value="5">Edit</button>
    </div></tr>

    <tr><div>
        <td><p><a href="http://www.timeanddate.com/countdown/to?iso=20191227T17&amp;p0=843&amp;msg=retirement&amp;swk=1">retirement countdown</a>
            <br>the number of weeks I have until retirement</p>
        <td><button type=submit name="delete" value="6">Delete</button>
        <td><button type=submit name="edit" value="6">Edit</button>
    </div></tr>

  </table>
  </form>

  <br><a href="/bookmark">new bookmark</a>


</body>
</html>
""")
    f.close()


# -----------------------------------------------------------------------------
def fns_launch(args):
    """launch - start the app
    """
    start_up(debug=True)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main(sys.argv)

