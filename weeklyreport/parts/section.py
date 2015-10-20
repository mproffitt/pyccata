"""
Create a new section
"""
from weeklyreport.managers.report import ReportManager
from weeklyreport.abstract import ThreadableDocument
from weeklyreport.decorators import accepts
from weeklyreport.factory import DocumentPartFactory
from weeklyreport.log import Logger

class Section(ThreadableDocument):
    """ Create a new section for the document """
    PRIORITY = 1
    _structure = None
    _title = None
    _abstract = None
    _factory = None
    _level = None

    @accepts(title=str, abstract=str, level=int, structure=(None, list))
    def setup(self, title='', abstract='', level=0, structure=None):
        """ Set up the section object """

        # pylint: disable=arguments-differ
        # The parent class defines this method using *args, **kwargs
        # but then calls back on this method using reflection
        # in order to bind the configuration.
        # As a result, the arguments will always differ.

        self._factory = DocumentPartFactory()
        self._title = title
        self._abstract = self._factory.abstract(abstract)
        self._structure = self._parse_structure(structure)
        self.level = level

    @property
    def level(self):
        """ Get the current section heading level """
        return self._level

    @level.setter
    @accepts(int)
    def level(self, level):
        """
        Set the current section heading level

        @param level int
        """
        self._level = level

    def run(self):
        """ Execute the thread """
        pass

    @accepts(ReportManager)
    def render(self, report):
        """ render the current object """
        report.add_heading(self._title, self.level)
        self._abstract.render(report)
        for part in self._structure:
            part.render(report)

    @accepts((None, list))
    def _parse_structure(self, config):
        """
        Parses the provided configuration and converts it
        to a document structure

        @param config list A list of items defining the section content
        """
        structure = []
        if config is not None:
            for item in config:
                name = getattr(self._factory, item.type)
                args = item.content

                # pylint: disable=broad-except
                # anything can go wrong when adding a new item.
                # we need to record what did go wrong and move on
                try:
                    structure.append(name(self.threadmanager, args))
                except Exception as exception:
                    Logger().warning('Failed to add item of type \'{0}\''.format(item.type))
                    Logger().warning('Reason was:')
                    Logger().warning(exception)
        return structure

