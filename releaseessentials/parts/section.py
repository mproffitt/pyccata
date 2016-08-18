"""
Create a new section
"""
from releaseessentials.managers.report import ReportManager
from releaseessentials.abstract import ThreadableDocument
from releaseessentials.decorators import accepts
from releaseessentials.factory import DocumentPartFactory
from releaseessentials.log import Logger
from releaseessentials.resources  import Replacements
from releaseessentials.parts.table import Table
from releaseessentials.filter import Filter

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
        """
        Execute the thread

        [DISABLED]
        Although Sections are threadable, generally we wouldn't require them to thread.
        Instead, section components are threaded.
        """
        pass

    @accepts(ReportManager)
    def render(self, report):
        """ render the current object """
        Logger().info('\033[1mWriting section {0}\033[0m'.format(self.title if self.title is not None else ''))
        if len(self._structure) > 0:
            using_tables = len(self._structure)
            for item in self._structure:
                if isinstance(item, Table) and isinstance(item.rows, Filter):
                    using_tables = using_tables - 1 if len(item.rows.results) == 0 else using_tables

            if using_tables == 0:
                # we probably have nothing to render
                Logger().info('Empty section. Skipping...')
                return

        report.add_heading(str(Replacements().replace(self._title)), self.level)
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
                title = getattr(item, 'title') if hasattr(item, 'title') else None

                # pylint: disable=broad-except
                # anything can go wrong when adding a new item.
                # we need to record what did go wrong and move on
                try:
                    component = name(self.threadmanager, args)
                    if title is not None:
                        component.title = title
                    structure.append(component)
                except Exception as exception:
                    Logger().warning('Failed to add item of type \'{0}\''.format(item.type))
                    Logger().warning(exception)
                    Logger().warning(args)
        return structure
