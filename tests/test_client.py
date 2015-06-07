from __future__ import unicode_literals

import pytest
from builtins import bytes
from Crypto.Cipher import AES

from bugbuzz import BugBuzzClient


def pkcs5_unpad(data):
    """Do PKCS5 unpadding to data and return

    """
    data_bytes = bytes(data)
    return data_bytes[0:-data_bytes[-1]]


@pytest.fixture
def bugbuzz_client(base_url='http://localhost'):
    return BugBuzzClient(base_url)


def test_random_access_key():
    keys = set()
    for _ in range(100):
        client = bugbuzz_client()
        keys.add(client.aes_key)
    assert len(keys) == 100


def test_encrypt_decrypt(bugbuzz_client):
    plaintext = b'super foobar'
    iv, encrypted = bugbuzz_client.encrypt(plaintext)
    assert encrypted != plaintext

    aes = AES.new(bugbuzz_client.aes_key, AES.MODE_CBC, iv)
    assert pkcs5_unpad(aes.decrypt(encrypted)) == plaintext
