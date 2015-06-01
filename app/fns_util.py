import time
import pdb
from app import Bookmark


# -----------------------------------------------------------------------------
def bm_list(owner_id, db):
    # pdb.set_trace()
    z = db.session.query(Bookmark).filter_by(owner=owner_id).all()
    return z


# -----------------------------------------------------------------------------
def pu_time(reset=False):
    """
    Return True if we've been called at least 3 times in the last minute
    """
    if reset:
        pu_time.queue = []
        return False

    now = time.time()
    try:
        pu_time.queue.append(now)
    except AttributeError:
        pu_time.queue = [now]

    pu_time.queue = [x for x in pu_time.queue if now - x < 60]
    print pu_time.queue
    if len(pu_time.queue) < 5:
        return False
    return True
