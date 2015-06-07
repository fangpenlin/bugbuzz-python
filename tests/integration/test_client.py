from __future__ import unicode_literals

from future.standard_library import install_aliases
install_aliases()

import json
import base64
from urllib import parse as urlparse

import pytest
from Crypto.Cipher import AES

from bugbuzz.client import BugBuzzClient
from bugbuzz.packages import requests
from ..helpers import pkcs5_unpad


@pytest.fixture(scope='session')
def bugbuzz_client(base_url='https://bugbuzz-api.herokuapp.com'):
    client = BugBuzzClient(base_url)
    client.start()
    return client


@pytest.fixture(scope='session')
def source_file(bugbuzz_client):
    with open(__file__, 'rb') as source_file:
        source = source_file.read()
    uploaded_file = bugbuzz_client.upload_source(__file__, source)
    return source, uploaded_file


def test_creating_session(bugbuzz_client):
    bugbuzz_client.start()
    assert bugbuzz_client.session_id.startswith('SE')
    url = urlparse.urljoin(
        bugbuzz_client.base_url,
        '/sessions/{}'.format(bugbuzz_client.session_id),
    )
    resp = requests.get(url)
    session = resp.json()['session']
    assert session['encrypted']
    assert session.get('validation_code')
    assert session.get('aes_iv')


def test_upload_source(bugbuzz_client, source_file):
    source, uploaded_file = source_file

    url = urlparse.urljoin(
        bugbuzz_client.base_url,
        '/files/{}'.format(uploaded_file['id']),
    )
    resp = requests.get(url)
    file_ = resp.json()['file']
    assert file_['session'] == bugbuzz_client.session_id

    iv = base64.b64decode(file_['aes_iv'].encode('latin1'))
    content = base64.b64decode(file_['content'].encode('latin1'))
    aes = AES.new(bugbuzz_client.aes_key, AES.MODE_CBC, iv)
    assert pkcs5_unpad(aes.decrypt(content)) == source


def test_add_break(bugbuzz_client, source_file):
    source, uploaded_file = source_file
    local_vars = dict(foo='bar', eggs='spam')
    created_break_ = bugbuzz_client.add_break(
        73,
        uploaded_file['id'],
        local_vars,
    )

    url = urlparse.urljoin(
        bugbuzz_client.base_url,
        '/breaks/{}'.format(created_break_['id']),
    )
    resp = requests.get(url)
    break_ = resp.json()['break']
    assert break_['session'] == bugbuzz_client.session_id
    assert break_['lineno'] == 73
    assert break_['file'] == uploaded_file['id']

    iv = base64.b64decode(break_['aes_iv'].encode('latin1'))
    encrypted = base64.b64decode(break_['local_vars'].encode('latin1'))
    aes = AES.new(bugbuzz_client.aes_key, AES.MODE_CBC, iv)
    parsed_local_vars = json.loads(
        pkcs5_unpad(aes.decrypt(encrypted)).decode('latin1')
    )
    assert parsed_local_vars == local_vars
