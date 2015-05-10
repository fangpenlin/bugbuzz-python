from __future__ import unicode_literals
import sys
import bdb
import time
import threading
import urlparse
import urllib
import logging
import Queue

# TODO: use a embedded requests package or use urllib instead?
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
        # TODO: handle error
        self.session_id = resp.json()['id']
        self.event_thread.start()

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

    def __init__(self, base_url):
        bdb.Bdb.__init__(self)
        self.client = BugBuzzClient(base_url)
        self.client.start()

    def interaction(self, frame, traceback=None):
        cmd = self.client.cmd_queue.get(True)
        cmd_type = cmd['type']
        if cmd_type == 'next':
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
        logger.debug('User call')
        self.interaction(frame)

    def user_line(self, frame):
        """This method is called when we stop or break at this line.

        """
        logger.debug('User line')
        self.interaction(frame)

    def user_return(self, frame, return_value):
        """This method is called when a return trap is set here.

        """
        logger.debug('User return')
        self.interaction(frame)

    def user_exception(self, frame, exc_info):
        """This method is called if an exception occurs,
        but only if we are to stop at or just below this level.

        """
        logger.debug('User exception')
        exc_type, exc_value, exc_traceback = exc_info
        self.interaction(frame, exc_traceback)


def set_trace():
    BugBuzz('http://127.0.0.1:9090').set_trace(sys._getframe().f_back)
