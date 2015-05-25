from __future__ import unicode_literals

import base64
import bdb
import inspect
import json
import logging
import os
import Queue
import sys
import urllib
import urlparse
import uuid
import webbrowser

from Crypto import Random
from Crypto.Cipher import AES

from .packages import pubnub
from .packages import requests

logger = logging.getLogger(__name__)

__version__ = '0.0.1'

BLOCK_SIZE = 16


def pkcs5_pad(string):
    """Do PKCS5 padding to string and return

    """
    return (
        string +
        (BLOCK_SIZE - len(string) % BLOCK_SIZE) *
        chr(BLOCK_SIZE - len(string) % BLOCK_SIZE)
    )


def pkcs5_unpad(string):
    """Do PKCS5 unpadding to string and return

    """
    return string[0:-ord(string[-1])]


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
        self.cmd_queue = Queue.Queue()
        # generate AES encryption key
        self.rndfile = Random.new()
        self.aes_key = self.rndfile.read(32)

    def _api_url(self, path):
        """API URL for path

        """
        return urlparse.urljoin(self.base_url, path)

    def encrypt(self, content):
        """Encrypt a given content and return (iv, encrypted content)

        """
        iv = self.rndfile.read(16)
        aes = AES.new(self.aes_key, AES.MODE_CBC, iv)
        return iv, aes.encrypt(pkcs5_pad(content))

    def start(self):
        # validation code is for validating given access key correct or not
        validation_code = uuid.uuid4().hex
        iv, encrypted_code = self.encrypt(validation_code)
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
        iv, encrpyted = self.encrypt(json.dumps(local_vars))
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


class BugBuzz(bdb.Bdb, object):

    QUEUE_POLLING_TIMEOUT = 10

    VAR_VALUE_TRUNCATE_SIZE = 1024

    @classmethod
    def dump_vars(cls, vars):
        """Dump vars dict as name to repr string

        """
        def strip(value):
            try:
                return repr(value)[:cls.VAR_VALUE_TRUNCATE_SIZE]
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                return '<Error>'
        return dict((key, strip(value)) for key, value in vars.iteritems())

    def __init__(self, base_url, dashboard_url):
        bdb.Bdb.__init__(self)
        self.dashboard_url = dashboard_url
        self.client = BugBuzzClient(base_url)
        # map filename to uploaded files
        self.uploaded_sources = {}
        # current frame object
        self.current_frame = None

    def upload_source(self, frame):
        """Upload source code if it is not available on server yet

        """
        # TODO: what if the filename is not unicode?
        filename = unicode(frame.f_code.co_filename)
        if filename in self.uploaded_sources:
            return self.uploaded_sources[filename]
        logger.info('Uploading %s', filename)
        source_lines, _ = inspect.findsource(frame.f_code)
        uploaded = self.client.upload_source(
            filename=filename,
            content=b''.join(source_lines),
        )
        self.uploaded_sources[filename] = uploaded
        return uploaded

    def set_trace(self, frame):
        self.current_frame = frame
        self.client.start()
        access_key = base64.urlsafe_b64encode(self.client.aes_key)
        session_url = urlparse.urljoin(
            self.dashboard_url,
            '/#/sessions/{}?{}'.format(
                self.client.session_id,
                urllib.urlencode(dict(access_key=access_key)),
            )
        )
        print >>sys.stderr, 'Access Key:', access_key
        print >>sys.stderr, 'Dashboard URL:', session_url
        webbrowser.open_new_tab(session_url)
        file_ = self.upload_source(self.current_frame)
        # TODO: handle filename is None or other situations?
        self.client.add_break(
            file_id=file_['id'],
            lineno=self.current_frame.f_lineno,
            local_vars=self.dump_vars(self.current_frame.f_locals),
        )
        bdb.Bdb.set_trace(self, frame)

    def interaction(self, frame, traceback=None):
        self.current_frame = frame
        file_ = self.upload_source(self.current_frame)
        # TODO: handle filename is None or other situations?
        self.client.add_break(
            file_id=file_['id'],
            lineno=self.current_frame.f_lineno,
            local_vars=self.dump_vars(self.current_frame.f_locals),
        )

        cmd = None
        while cmd is None:
            try:
                # Notice: we need to specify a timeout, otherwise the get
                # operation cannot be interrupted
                cmd = self.client.cmd_queue.get(
                    True,
                    self.QUEUE_POLLING_TIMEOUT,
                )
            except (KeyboardInterrupt, SystemExit):
                raise
            except Queue.Empty:
                continue
        cmd_type = cmd['type']
        if cmd_type == 'return':
            self.set_return(frame)
        elif cmd_type == 'next':
            self.set_next(frame)
        elif cmd_type == 'step':
            self.set_step()
        elif cmd_type == 'continue':
            self.set_continue()

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function.

        """
        logger.debug(
            'User call, %s:%s',
            frame.f_code.co_filename,
            frame.f_lineno
        )
        self.interaction(frame)

    def user_line(self, frame):
        """This method is called when we stop or break at this line.

        """
        logger.debug(
            'User line, %s:%s',
            frame.f_code.co_filename,
            frame.f_lineno
        )
        self.interaction(frame)

    def user_return(self, frame, return_value):
        """This method is called when a return trap is set here.

        """
        logger.debug(
            'User return, %s:%s',
            frame.f_code.co_filename,
            frame.f_lineno
        )
        self.interaction(frame)

    def user_exception(self, frame, exc_info):
        """This method is called if an exception occurs,
        but only if we are to stop at or just below this level.

        """
        logger.debug(
            'User exception, %s:%s',
            frame.f_code.co_filename,
            frame.f_lineno
        )
        exc_type, exc_value, exc_traceback = exc_info
        self.interaction(frame, exc_traceback)


def set_trace():
    api_url = os.getenv('BUGBUZZ_API', 'https://bugbuzz-api.herokuapp.com')
    db_url = os.getenv(
        'BUGBUZZ_DASHBOARD',
        'http://dashboard.bugbuzz.io/'
    )
    BugBuzz(api_url, db_url).set_trace(sys._getframe().f_back)
