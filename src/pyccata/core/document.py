"""
Document controller module
"""
from pyccata.core.abstract import ControllerAbstract
from pyccata.core.exceptions import ThreadFailedError
from pyccata.core.configuration import Configuration
from pyccata.core.factory import DocumentPartFactory
from pyccata.core.log import Logger
from pyccata.core.decorators import accepts

class DocumentController(ControllerAbstract):
    """
    The document controller class brings together
    the configuration of the document with the methods
    for obtaining the information defined as being
    provided in the report.
    """
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

