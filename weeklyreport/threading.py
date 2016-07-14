"""
Base classes for any items which need to be run in their own thread.
"""

from abc import abstractmethod
from threading import Thread
from weeklyreport.decorators import accepts

class Threadable(Thread):
    """
    Base class for threadable objects
    """

    THREAD_SLEEP = 0.01
    PRIORITY = 0

    _complete = False
    _failure = None
    _retrycount = 0

    @property
    def failed(self):
        """ Did execution of this thread fail? """
        return self._failure is not None

    @property
    def failure(self):
        """ Get the exception stating why the thread failed """
        return self._failure

    @failure.setter
    @accepts(Exception)
    def failure(self, reason):
        """ Set the exception showing why the thread failed """
        self._failure = reason

    @property
    def complete(self):
        """ Has the current thread completed its run? """
        return self._complete

    @property
    def ready(self):
        """ Is the thread ready to start? """
        return not self.isAlive() and not (self.complete or self.failed)

    @abstractmethod
    def setup(self, *args, **kwargs):
        """ Called from __init__ this method sets up the current object """
        raise NotImplementedError('Method must be implemented by a child')

    def __init__(self, *args, **kwargs):
        """
        Initialise the current thread
        """
        self.setup(*args, **kwargs)
        Thread.__init__(self)

    @abstractmethod
    def run(self):
        """
        Trigger the current thread and any downstream threads

        Any exceptions raised within the run method must be handled
        here and assigned to the failure as a reason. This is to allow
        the parent thread to understand the reason a given thread failed
        """
        raise NotImplementedError('Method must be implemented by a child')
