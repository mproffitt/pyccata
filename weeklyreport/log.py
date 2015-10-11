import sys
from weeklyreport.decorators import accepts
from weeklyreport.interface  import ViewWindowInterface

class Logger(object):
    DEBUG     = "\033[36m[DEBUG]\033[00m "
    INFO      = "[INFO] "
    WARNING   = "\033[33m[WARNING]\033[00m "
    ERROR     = "\033[31m[ERROR]\033[00m "
    FATAL     = "\033[31m[FATAL]\033[00m "
    INPUT     = 5

    _suppress = False
    _view     = None
    _input    = None
    _requires_newline = False

    @property
    def suppress(self):
        return self._suppress

    @suppress.setter
    def suppress(self, value):
        self._suppress = value

    @property
    def stdout(self):
        return self._view

    @stdout.setter
    @accepts((sys.stderr, sys.stdout, ViewWindowInterface))
    def stdout(self, value):
        self._view = value

    @property
    def stdin(self):
        return self._input

    @stdin.setter
    @accepts((sys.stdin, ViewWindowInterface))
    def stdin(self, value):
        self._input = value

    def __init__(self, view = sys.stderr, input=sys.stdin):
        self.stdout  = view
        self.stdin   = input

    def log(self, level, message):
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
        self.log(self.DEBUG, message)

    def info(self, message):
        self.log(self.INFO, message)

    def warning(self, message):
        self.log(self.WARNING, message)

    def error(self, message):
        self.log(self.ERROR, message)

    def fatal(self, message):
        self.log(self.FATAL, message)

    def input(self, message):
        return self.log(self.INPUT, message)

    def append(self, message):
        self.stdout.write('.')
        self.stdout.flush()
        self._requires_newline = True

    _instance = None
    def __new__(cls):
        if Logger._instance is None:
            Logger._instance = object.__new__(cls)
        return Logger._instance


