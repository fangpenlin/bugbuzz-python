# -*- coding: utf8 -*-
from __future__ import unicode_literals

from future.standard_library import install_aliases
install_aliases()

import sys
import time
import threading
from urllib import parse as urlparse

import pytest

from bugbuzz import BugBuzz
from bugbuzz.packages import requests

# just a dummy unicode string, to see if we can handle unicode correctly
DUMMY_STR = u'除錯'


@pytest.fixture(scope='session')
def bugbuzz_dbg(
    base_url='https://bugbuzz-api.herokuapp.com',
    dashboard_url='http://dashboard.bugbuzz.io/',
):
    return BugBuzz(base_url, dashboard_url)


def test_set_trace(mocker, bugbuzz_dbg):
    mocker.patch('webbrowser.open_new_tab')

    # post continue command
    def post_continue():
        time.sleep(3)
        url = urlparse.urljoin(
            bugbuzz_dbg.base_url,
            '/sessions/{}/actions/continue'.format(
                bugbuzz_dbg.client.session_id
            ),
        )
        requests.post(url)

    thread = threading.Thread(target=post_continue)
    thread.daemon = True
    thread.start()

    # TODO: set a timeout here?
    bugbuzz_dbg.set_trace(sys._getframe())

    url = urlparse.urljoin(
        bugbuzz_dbg.base_url,
        '/sessions/{}'.format(bugbuzz_dbg.client.session_id),
    )
    resp = requests.get(url)
    session = resp.json()['session']
    assert len(session['files']) == 1
    assert len(session['breaks']) == 1
