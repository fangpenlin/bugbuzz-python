from __future__ import unicode_literals
import sys
import bdb


class BugBuzz(bdb.Bdb):

    def interaction(self, frame, traceback=None):
        cmd = raw_input('cmd:')
        if cmd == 's':
            self.set_step()
        elif cmd == 'n':
            self.set_next(frame)

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        print 'user_call', frame
        self.interaction(frame)

    def user_line(self, frame):
        """This method is called when we stop or break at this line."""
        print 'user_line', frame
        self.interaction(frame)

    def user_return(self, frame, return_value):
        """This method is called when a return trap is set here."""
        print 'user_return', frame

    def user_exception(self, frame, exc_info):
        exc_type, exc_value, exc_traceback = exc_info
        """This method is called if an exception occurs,
        but only if we are to stop at or just below this level."""
        print 'user_exception', frame



def set_trace():
    BugBuzz().set_trace(sys._getframe().f_back)
