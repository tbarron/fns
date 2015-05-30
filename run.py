#!/usr/bin/env python
from app import app, init_db
import pdb

# pdb.set_trace()
init_db()
app.run(debug=True)
