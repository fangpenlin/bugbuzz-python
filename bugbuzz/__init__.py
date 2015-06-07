from __future__ import unicode_literals

import os
import sys

__version__ = '0.1.2'


def set_trace():
    from .debugger import BugBuzz
    api_url = os.getenv('BUGBUZZ_API', 'https://bugbuzz-api.herokuapp.com')
    db_url = os.getenv(
        'BUGBUZZ_DASHBOARD',
        'http://dashboard.bugbuzz.io/'
    )
    BugBuzz(api_url, db_url).set_trace(sys._getframe().f_back)
