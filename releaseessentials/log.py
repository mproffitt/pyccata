"""
Provides a simple logging mechanism to be used
throughout the releaseessentials package
"""
import sys
from releaseessentials.decorators import accepts
from releaseessentials.interface  import ViewWindowInterface

class Logger(object):
    """
    Provides methods of writing messages to a given interface and
    reading from a provided input.

    By default the output from this class is sent to stderr although
    this can be configured at any time to be written to a different
    interface (stdout, custom).

    Where a custom view is required, this must implement the
    ViewWindowInterface interface class.
    """
    DEBUG = "\033[36m[DEBUG]\033[00m "
    INFO = "[INFO] "
    WARNING = "\033[33m[WARNING]\033[00m "
    ERROR = "\033[31m[ERROR]\033[00m "
    FATAL = "\033[31m[FATAL]\033[00m "
    INPUT = 5

    _suppress = False
    _view = None
    _input = None
    _requires_newline = False
    _is_loaded = False

    @property
    def suppress(self):
        """ Are we preventing messages from being written? """
        return self._suppress

    @suppress.setter
    @accepts(bool)
    def suppress(self, value):
        """ Enable or disable message suppression """
        self._suppress = value

    @property
    def stdout(self):
        """ Get the current log output window """
        return self._view

    @stdout.setter
    @accepts((sys.stderr, sys.stdout, ViewWindowInterface))
    def stdout(self, value):
        """
        Set the current view output window

        @param value [sys.stdout, sys.stderr, ViewWindowInterface]
        """
        self._view = value

    @property
    def stdin(self):
        """ Get the current log input interface """
        return self._input

    @stdin.setter
    @accepts((sys.stdin, ViewWindowInterface))
    def stdin(self, value):
        """
        Set the current log input interface

        @param value [sys.stdout, sys.stderr, ViewWindowInterface]
        """
        self._input = value

    def __init__(self, view=sys.stderr, stdin=sys.stdin):
        """
        Initialise the Logger

        @param view [sys.stdout, sys.stderr, ViewWindowInterface] (default sys.stderr)
        @param view [sys.stdin, ViewWindowInterface] (default sys.stdin)
        """
        if self._is_loaded:
            return
        self.stdout = view
        self.stdin = stdin
        self._is_loaded = True

    def log(self, level, message):
        """
        Default logging method

        @param level   const
        @param message string
        """
        if self.suppress:
            return
        if level == self.INPUT:
            message = self.INFO + str(message) + ' > '

            write_to = self.stdin
            if self.stdin is sys.stdin:
                write_to = self.stdout

            write_to.write(message)
            write_to.flush()
            return self.stdin.readline().strip()
        else:
            self.stdout.write(level  + str(message)   + "\n")
            self.stdout.flush()

    def debug(self, message):
        """
        Write debug messages to the output

        @param message string
        """
        self.log(self.DEBUG, message)

    def info(self, message):
        """
        Write info messages to the output

        @param message string
        """
        self.log(self.INFO, message)

    def warning(self, message):
        """
        Write warning messages to the output

        @param message string
        """
        self.log(self.WARNING, message)

    def error(self, message):
        """
        Write error messages to the output

        @param message string
        """
        self.log(self.ERROR, message)

    def fatal(self, message):
        """
        Write fatal messages to the output

        @param message string
        """
        self.log(self.FATAL, message)

    def input(self, message=''):
        """
        Get input from the user

        @param message string [optional] (default empty)

        @return string
        """
        return self.log(self.INPUT, message)

    def append(self, message='.'):
        """
        Append a message to the output without adding a newline

        By default the log method writes a newline character after message.
        If you do not wish to have the newline character embedded, call this
        method instead.

        @param message string
        """
        self.stdout.write(message)
        self.stdout.flush()
        self._requires_newline = True

    _instance = None
    def __new__(cls, *args, **kwargs):
        # pylint: disable=unused-argument
        # handled by call to parent
        """ Set up a singleton instance of the Logger """
        if Logger._instance is None:
            Logger._instance = super(Logger, cls).__new__(cls)
        return Logger._instance
