"""
Document controller module
"""
from weeklyreport.exceptions import InvalidClassError
from weeklyreport.exceptions import InvalidModuleError
from weeklyreport.exceptions import RequiredKeyError
from weeklyreport.configuration import Configuration
from weeklyreport.managers.thread import ThreadManager
from weeklyreport.managers.report import ReportManager
from weeklyreport.factory import DocumentPartFactory
from weeklyreport.log import Logger
from weeklyreport.decorators import accepts

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

    def __init__(self):
        """ Initialise the document """
        self._configuration = self.configuration
        self._thread_manager = self.threadmanager
        self._report_manager = self.reportmanager
        self._part_factory = self.partfactory
        self._sections = []

    @property
    def configuration(self):
        """ Load the configuration from file """
        try:
            if self._configuration is None:
                return Configuration()
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

        self.threadmanager.start()
        if self.threadmanager.completed:
            self.reportmanager.create_title_page()
            for section in self._sections:
                section.render(self._report_manager)

    @accepts(str)
    def save(self, filename):
        """ Save the current report """
        self.reportmanager.save(filename)

    @staticmethod
    def _raise_and_terminate(what, exception):
        """ Log any exceptions raised and terminate the application """
        Logger().fatal('Unable to instantiate the {0}.'.format(what))
        Logger().fatal('exception message was:')
        Logger().fatal(str(exception))
        raise exception

