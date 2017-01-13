"""
Container for all abstract classes defined by the application
"""
import os
import sys
import inspect
import importlib
from abc import abstractmethod
from abc import abstractproperty
from collections import namedtuple
from pyccata.core.decorators import accepts
from pyccata.core.configuration import Configuration
from pyccata.core.exceptions import RequiredKeyError
from pyccata.core.exceptions import InvalidModuleError
from pyccata.core.exceptions import InvalidClassError
from pyccata.core.threading import Threadable
from pyccata.core.managers.thread import ThreadManager
from pyccata.core.managers.report import ReportManager
from pyccata.core.interface import ManagerInterface
from pyccata.core.log import Logger

class ControllerAbstract(object):
    """
    Any controller classes must implement this class
    """
    _part_factory = None
    _configuration = None
    _thread_manager = None
    _report_manager = None
    _configuration_file = ''

    def __init__(self, configuration_file='configuration.json'):
        """ Initialise the document """
        self._configuration_file = configuration_file

        self._configuration = self.configuration
        self._thread_manager = self.threadmanager
        self._report_manager = self.reportmanager
        self._part_factory = self.partfactory
        self._sections = []

    def add_callback(self, name, function):
        """
        Adds a callback onto the report manager

        @param name string
        @param function method signature
        """
        self._report_manager.add_callback(name, function)

    @property
    def configuration(self):
        """ Load the configuration from file """
        try:
            if self._configuration is None:
                return Configuration(filename=self._configuration_file)
        except (InvalidClassError, InvalidModuleError, RequiredKeyError, AttributeError, IOError) as exception:
            ControllerAbstract._raise_and_terminate('Configuration object', exception)
        return self._configuration

    @property
    def threadmanager(self):
        """ Load the threadmanager """
        try:
            if self._thread_manager is None:
                return ThreadManager()
        except (ImportError, AttributeError, NotImplementedError, RequiredKeyError) as exception:
            ControllerAbstract._raise_and_terminate('ThreadManager', exception)
        return self._thread_manager

    @property
    def reportmanager(self):
        """ load the reportmanager """
        try:
            if self._report_manager is None:
                return ReportManager()
        except (ImportError, AttributeError, NotImplementedError, RequiredKeyError) as exception:
            ControllerAbstract._raise_and_terminate('ReportManager', exception)
        return self._report_manager

    @staticmethod
    def _raise_and_terminate(what, exception):
        """ Log any exceptions raised and terminate the application """
        Logger().fatal('Unable to instantiate the {0}.'.format(what))
        Logger().fatal('exception message was:')
        Logger().fatal(str(exception))
        raise exception

    @abstractmethod
    def build(self):
        """ Builds the current controller """
        raise NotImplementedError('`build` must be implemented by a child class')

    @abstractmethod
    def save(self, filename):
        """ saves the current controller """
        raise NotImplementedError('`save` method must be implemented by a child class')

class ThreadableDocument(Threadable):
    """
    Any objects which need to be renderable must implement this class
    """
    MAX_DOCUMENT_PRIORITY = 100
    PRIORITY = 0
    _title = None

    @accepts(ThreadManager, tuple)
    def __init__(self, threadmanager, config):
        """
        Initialise the ThreadableDocument object
        """
        self._thread_manager = threadmanager

        # we are now in a seperate thread, This will not have a configuration
        # pylint: disable=protected-access
        # verification that Configuration is not initialised and initialise it
        # with the thread manager - this is desired behaviour against the singleton
        # to prevent it being loaded multiple times inside threading objects
        if Configuration._instance is None:
            Configuration._instance = self.threadmanager.configuration

        self.validate_setup(config)
        # No Document priority can be greater than MAX_DOCUMENT_PRIORITY
        # This is to ensure Filter instances are always executed first.
        if getattr(self, 'PRIORITY') > ThreadableDocument.MAX_DOCUMENT_PRIORITY:
            setattr(self, 'PRIORITY', ThreadableDocument.MAX_DOCUMENT_PRIORITY)

        super().__init__(**config._asdict())
        self.threadmanager.append(self)


    @property
    def title(self):
        """ gets the list title """
        return self._title

    @title.setter
    def title(self, title):
        """ sets the list title """
        self._title = title


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

class ManagableAbstract(object):
    """
    Managers should extend this class
    """
    # pylint: disable=too-few-public-methods
    # This is a basic inheritance point which doesn't
    # require many methods
    __implements__ = (ManagerInterface,)
    _client = None
    _configuration = None
    _options = {}

    MAX_RESULTS = 50

    @property
    def configuration(self):
        """
        Lazy load the Configuration singleton instance

        @return Configuration
        """
        if self._configuration is None:
            self._configuration = Configuration()
        return self._configuration

class FactoryAbstract(list):
    """
    The part factory provides methods of getting the
    different document sections used by the application.

    Valid document parts are stored inside the parts
    module and extend ThreadableDocument as being their
    primary base class. This helps ensure all parts can
    be built correctly and utilise threads where possible.

    If your part does not require threading, add an empty
    ``run`` method

    ThreadableDocument parts must not provide their own
    __init__ method unless super().__init__ is called.

    Instead, ThreadableDocument.__init__ calls back onto
    a ``setup`` method which should be defined within your
    class

    Example:

        class MyDocumentPart(ThreadableDocument):
            def setup(self, *args, **kwargs):
                # do something here...

            def run(self):
                pass

            @accepts(ReportManager):
            def render(self, reportmanager)
                # render part
    """

    MODULE = 'parts'
    _instance = None
    _is_loaded = False
    _allowed = None

    @abstractproperty
    def allowed_class(self):
        """
        Gets the type of class allowed within this factory
        """
        raise NotImplementedError('allowed_class property must be returned by a child class')

    def __init__(self):
        """
        Load all ThreadableDocument extensions under [Configuration.NAMESPACE].parts

        @raise InvalidModuleError if the parts module cannot be found or loaded
        """
        if self._is_loaded:
            return

        self._allowed = [
            'abstract'
        ]

        super().__init__()
        part_loader = namedtuple('PartLoader', 'name cls')
        try:
            module_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), self.MODULE)
            files = [f for f in os.listdir(module_path) if os.path.isfile(os.path.join(module_path, f))]
        except FileNotFoundError:
            raise InvalidModuleError(self.MODULE, Configuration.NAMESPACE)

        clsnames = None
        for filename in files:
            module = os.path.splitext(filename)[0]
            module_name = Configuration.NAMESPACE + '.' + self.MODULE + '.' + module
            try:
                importlib.import_module(module_name)
            except ImportError:
                raise InvalidModuleError(self.MODULE, Configuration.NAMESPACE)
            clsnames = inspect.getmembers(sys.modules[module_name], inspect.isclass)
            for item in clsnames:
                name = item[0].lower()
                cls = item[1]
                if (cls.__module__ == module_name and (
                        issubclass(cls, self.allowed_class)
                        or module in self._allowed)):
                    self.append(part_loader(name=name, cls=cls))
        self._is_loaded = True

    def __getattr__(self, name):
        for item in self:
            if item.name == name:
                return item.cls
        raise InvalidClassError(name, Configuration.NAMESPACE + '.' + self.MODULE)
