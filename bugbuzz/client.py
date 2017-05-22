from __future__ import print_function
from __future__ import unicode_literals

from future.standard_library import install_aliases
install_aliases()

import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import uuid  # noqa: E402
import queue  # noqa: E402
from urllib import parse as urlparse  # noqa: E402

from Crypto.Cipher import AES  # noqa: E402

from .packages import pubnub  # noqa: E402
from .packages import requests  # noqa: E402

logger = logging.getLogger(__name__)


BLOCK_SIZE = 16


def pkcs5_pad(data):
    """Do PKCS5 padding to data and return

    """
    remain = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + (remain * chr(remain).encode('latin1'))


class BugBuzzClient(object):

    """BugBuzzClient talks to BugBuzz server and response commands

    """

    def __init__(self, base_url):
        self.base_url = base_url
        self.running = True
        # requests session
        self.req_session = requests.Session()
        self.pubnub = None
        # debugging session ID
        self.session_id = None
        # last event timestamp
        self.last_timestamp = None
        # thread for polling events from server
        self.cmd_queue = queue.Queue()
        # generate AES encryption key
        self.aes_key = os.urandom(32)

    def _api_url(self, path):
        """API URL for path

        """
        return urlparse.urljoin(self.base_url, path)

    def encrypt(self, content):
        """Encrypt a given content and return (iv, encrypted content)

        """
        from builtins import bytes
        if not isinstance(content, bytes):
            raise TypeError('Content needs to be bytes')
        iv = os.urandom(16)
        aes = AES.new(self.aes_key, AES.MODE_CBC, iv)
        return iv, aes.encrypt(pkcs5_pad(content))

    def start(self):
        # validation code is for validating given access key correct or not
        validation_code = uuid.uuid4().hex
        iv, encrypted_code = self.encrypt(validation_code.encode('latin1'))
        # talk to server, register debugging session
        resp = self.req_session.post(
            self._api_url('sessions'),
            dict(
                encrypted='true',
                validation_code=validation_code,
            ),
            files=dict(
                encrypted_code=('encrypted_code', encrypted_code),
                aes_iv=('aes_iv', iv),
            ),
        )
        resp.raise_for_status()
        # TODO: handle error
        session = resp.json()['session']
        self.session_id = session['id']
        self.pubnub = pubnub.Pubnub(
            publish_key='',
            subscribe_key=session['pubnub_subscribe_key'],
            ssl_on=True,
            daemon=True,
        )
        self.pubnub.subscribe(
            session['client_channel'],
            callback=self.process_event,
        )

    def add_break(self, lineno, file_id, local_vars):
        """Add a break to notify user we are waiting for commands

        """
        logger.info('Add break lineno=%s, file_id=%s', lineno, file_id)
        url = self._api_url('sessions/{}/breaks'.format(self.session_id))
        iv, encrpyted = self.encrypt(json.dumps(local_vars).encode('latin1'))
        resp = self.req_session.post(
            url,
            dict(
                lineno=str(lineno),
                file_id=file_id,
            ),
            files=dict(
                local_vars=('local_vars', encrpyted),
                aes_iv=('aes_iv', iv),
            ),
        )
        resp.raise_for_status()
        return resp.json()['break']

    def upload_source(self, filename, content):
        """Uplaod source code to server

        """
        url = self._api_url('sessions/{}/files'.format(self.session_id))
        iv, encrpyted = self.encrypt(content)
        resp = self.req_session.post(
            url,
            files=dict(
                file=(filename, encrpyted),
                aes_iv=('aes_iv', iv),
            ),
        )
        resp.raise_for_status()
        return resp.json()['file']

    def process_event(self, message, channel):
        """Process events from the server

        """
        event = message['event']
        logger.debug('Events: %r', event)
        # TODO: process source code requests
        # TODO: process other requests
        self.cmd_queue.put_nowait(event)
