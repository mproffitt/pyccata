"""
Container for all abstract classes defined by the application
"""
import inspect
from abc import abstractmethod
from releaseessentials.decorators import accepts
from releaseessentials.exceptions import ArgumentMismatchError
from releaseessentials.managers.thread import ThreadManager
from releaseessentials.configuration import Configuration

from releaseessentials.threading import Threadable

class ThreadableDocument(Threadable):
    """
    Any objects which need to be renderable must implement this class
    """
    MAX_DOCUMENT_PRIORITY = 100
    PRIORITY = 0

    @accepts(ThreadManager, tuple)
    def __init__(self, threadmanager, config):
        """
        Initialise the ThreadableDocument object
        """
        # pylint: disable=protected-access
        # protected access to _asdict() is requried
        # to iterate over namedtuples
        self._thread_manager = threadmanager

        # we are now in a seperate thread, This will not have a configuration
        if Configuration._instance is None:
            Configuration._instance = self.threadmanager.configuration

        setup_args = inspect.signature(self.setup)

        config_keys = [key for key in config._asdict()]
        setup_keys = [key for key in setup_args.parameters]

        if sorted(config_keys) != sorted(setup_keys):
            raise ArgumentMismatchError(
                self.__class__.__name__ + '.' + self.setup.__name__,
                config_keys,
                setup_keys
            )

        # No Document priority can be greater than MAX_DOCUMENT_PRIORITY
        # This is to ensure Filter instances are always executed first.
        if getattr(self, 'PRIORITY') > ThreadableDocument.MAX_DOCUMENT_PRIORITY:
            setattr(self, 'PRIORITY', ThreadableDocument.MAX_DOCUMENT_PRIORITY)

        super().__init__(**config._asdict())
        self.threadmanager.append(self)

    @property
    def threadmanager(self):
        """ Get the current loaded threadmanager """
        return self._thread_manager

    @abstractmethod
    def render(self, report):
        """
        Renders the current object into the report

        @param report ReportDocument
        """
        raise NotImplementedError('Method must be implemented by a child')
