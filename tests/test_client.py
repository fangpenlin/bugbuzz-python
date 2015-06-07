from __future__ import unicode_literals

import pytest

from bugbuzz import BugBuzzClient


@pytest.fixture
def bugbuzz_client(base_url='http://localhost'):
    return BugBuzzClient(base_url)


def test_random_access_key():
    keys = set()
    for _ in range(100):
        client = bugbuzz_client()
        keys.add(client.aes_key)
    assert len(keys) == 100
