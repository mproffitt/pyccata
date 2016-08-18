"""
Document controller module
"""
from releaseessentials.exceptions import InvalidClassError
from releaseessentials.exceptions import InvalidModuleError
from releaseessentials.exceptions import RequiredKeyError
from releaseessentials.exceptions import ThreadFailedError
from releaseessentials.configuration import Configuration
from releaseessentials.managers.report import ReportManager
from releaseessentials.managers.thread import ThreadManager
from releaseessentials.factory import DocumentPartFactory
from releaseessentials.log import Logger
from releaseessentials.decorators import accepts

class DocumentController(object):
    """
    The document controller class brings together
    the configuration of the document with the methods
    for obtaining the information defined as being
    provided in the report.
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
            self._raise_and_terminate('Configuration object', exception)
        return self._configuration

    @property
    def threadmanager(self):
        """ Load the threadmanager """
        try:
            if self._thread_manager is None:
                return ThreadManager()
        except (ImportError, AttributeError, NotImplementedError, RequiredKeyError) as exception:
            self._raise_and_terminate('ThreadManager', exception)
        return self._thread_manager

    @property
    def reportmanager(self):
        """ load the reportmanager """
        try:
            if self._report_manager is None:
                return ReportManager()
        except (ImportError, AttributeError, NotImplementedError, RequiredKeyError) as exception:
            self._raise_and_terminate('ReportManager', exception)
        return self._report_manager

    @property
    def partfactory(self):
        """ get the factory used for creating document parts """
        if self._part_factory is None:
            return DocumentPartFactory()
        return self._part_factory

    def build(self):
        """ Build the report """
        for section in self.configuration.report.sections:
            self._sections.append(self.partfactory.section(self.threadmanager, section))

        # main build of document data
        self.threadmanager.start()

        if not self.threadmanager.completed:
            raise ThreadFailedError('Failed to build document due to invalid or incomplete threads')

        self.reportmanager.create_title_page()
        for section in self._sections:
            section.render(self._report_manager)

    def format_for_email(self):
        """
        Wraps the document inside a single table cell for display via email.
        """
        Logger().info('Wrapping document in table for email display')
        self.reportmanager.format_for_email()

    @accepts(str)
    def save(self, filename):
        """
        Save the current report

        @param filename string
        """
        Logger().info('Saving document to file')
        self.reportmanager.save(filename)
        Logger().info('Done')

    @staticmethod
    def _raise_and_terminate(what, exception):
        """ Log any exceptions raised and terminate the application """
        Logger().fatal('Unable to instantiate the {0}.'.format(what))
        Logger().fatal('exception message was:')
        Logger().fatal(str(exception))
        raise exception
