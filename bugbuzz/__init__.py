from __future__ import unicode_literals
import os
import sys
import bdb
import time
import threading
import urlparse
import urllib
import logging
import webbrowser
import Queue

# TODO: use a embedded requests package or use urllib instead?
import py
import requests

logger = logging.getLogger(__name__)


class BugBuzzClient(object):
    """BugBuzzClient talks to BugBuzz server and response commands

    """

    def __init__(self, base_url):
        self.base_url = base_url
        self.running = True
        # requests session
        self.req_session = requests.Session()
        # debugging session ID
        self.session_id = None
        # last event timestamp
        self.last_timestamp = None
        # thread for polling events from server
        self.event_thread = threading.Thread(target=self.poll_events)
        self.event_thread.daemon = True
        self.cmd_queue = Queue.Queue()

    def _api_url(self, path):
        """API URL for path

        """
        return urlparse.urljoin(self.base_url, path)

    def start(self):
        # talk to server, register debugging session
        resp = self.req_session.post(self._api_url('sessions'))
        resp.raise_for_status()
        # TODO: handle error
        self.session_id = resp.json()['id']
        self.event_thread.start()

    def add_break(self, lineno, file_id):
        """Add a break to notify user we are waiting for commands

        """
        logger.info('Add break lineno=%s, file_id=%s', lineno, file_id)
        url = self._api_url('sessions/{}/breaks'.format(self.session_id))
        resp = self.req_session.post(
            url,
            dict(
                lineno=lineno,
                file_id=file_id,
            ),
        )
        resp.raise_for_status()

    def upload_source(self, filename, content):
        """Uplaod source code to server

        """
        url = self._api_url('sessions/{}/files'.format(self.session_id))
        # TODO: what about encoding?
        resp = self.req_session.post(
            url,
            files=dict(file=(filename, content)),
        )
        resp.raise_for_status()
        return resp.json()['file']

    def poll_events(self):
        """Poll events from server in a thread

        """
        while self.running:
            # TODO: set timeout here
            # TODO: handle errors
            url = self._api_url('sessions/{}/events'.format(self.session_id))
            if self.last_timestamp is not None:
                url += '?' + urllib.urlencode(dict(
                    last_timestamp=self.last_timestamp
                ))
            resp = self.req_session.get(url)
            resp.raise_for_status()
            # TODO: use a better manner to handle long polling
            events = resp.json()['events']
            if not events:
                time.sleep(1)
                continue
            self.process_events(events)
            self.last_timestamp = events[-1]['created_at']

    def process_events(self, events):
        """Process events from the server

        """
        logger.info('Processing %s events from server ...', len(events))
        logger.debug('Events: %r', events)
        for event in events:
            # TODO: process source code requests
            # TODO: process other requests
            self.cmd_queue.put_nowait(event)


class BugBuzz(bdb.Bdb, object):

    def __init__(self, base_url, dashboard_url):
        bdb.Bdb.__init__(self)
        self.dashboard_url = dashboard_url
        self.client = BugBuzzClient(base_url)
        # map filename to uploaded files
        self.uploaded_sources = {}
        # current py.code.Frame object
        self.current_py_frame = None

    def upload_source(self, py_frame):
        """Upload source code if it is not available on server yet

        """
        filename = unicode(self.current_py_frame.code.path)
        if filename in self.uploaded_sources:
            return self.uploaded_sources[filename]
        logger.info('Uploading %s', filename)
        uploaded = self.client.upload_source(
            filename=filename,
            content=str(self.current_py_frame.code.fullsource).decode('utf8')
        )
        self.uploaded_sources[filename] = uploaded
        return uploaded

    def set_trace(self, frame):
        self.current_py_frame = py.code.Frame(frame)
        self.client.start()
        session_url = urlparse.urljoin(
            self.dashboard_url,
            '/sessions/{}'.format(self.client.session_id)
        )
        webbrowser.open_new_tab(session_url)
        file_ = self.upload_source(self.current_py_frame)
        # TODO: handle filename is None or other situations?
        self.client.add_break(
            file_id=file_['id'],
            lineno=self.current_py_frame.lineno + 1,
        )
        bdb.Bdb.set_trace(self, frame)

    def interaction(self, frame, traceback=None):
        self.current_py_frame = py.code.Frame(frame)
        file_ = self.upload_source(self.current_py_frame)
        # TODO: handle filename is None or other situations?
        self.client.add_break(
            file_id=file_['id'],
            lineno=self.current_py_frame.lineno + 1,
        )
        
        cmd = self.client.cmd_queue.get(True)
        cmd_type = cmd['type']
        if cmd_type == 'return':
            self.set_return(frame)
        elif cmd_type == 'next':
            self.set_next(frame)
        elif cmd_type == 'step':
            self.set_step()
        elif cmd_type == 'continue':
            self.set_continue()
        # TODO:

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