from __future__ import print_function
from __future__ import unicode_literals

from future.standard_library import install_aliases
install_aliases()

import base64
import bdb
import inspect
import logging
import sys
import webbrowser
import queue
from urllib import parse as urlparse

from .client import BugBuzzClient


logger = logging.getLogger(__name__)

__version__ = '0.1.2'

BLOCK_SIZE = 16


def pkcs5_pad(data):
    """Do PKCS5 padding to data and return

    """
    remain = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + (remain * chr(remain).encode('latin1'))


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
        return dict((key, strip(value)) for key, value in vars.items())

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
        filename = str(frame.f_code.co_filename)
        if filename in self.uploaded_sources:
            return self.uploaded_sources[filename]
        logger.info('Uploading %s', filename)
        source_lines, _ = inspect.findsource(frame.f_code)
        if source_lines:
            first_line = source_lines[0]
            if not isinstance(first_line, bytes):
                source_lines = map(
                    lambda line: line.encode('utf8'),
                    source_lines,
                )
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
                urlparse.urlencode(dict(access_key=access_key)),
            )
        )
        print('Access Key:', access_key, file=sys.stderr)
        print('Dashboard URL:', session_url, file=sys.stderr)
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
            except queue.Empty:
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
