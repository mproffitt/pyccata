"""
Contains the structure for creating tables
"""

from releaseessentials.managers.report import ReportManager
from releaseessentials.abstract import ThreadableDocument
from releaseessentials.decorators import accepts
from releaseessentials.filter import Filter
from releaseessentials.log import Logger
from releaseessentials.resources  import Replacements
from releaseessentials.configuration import Configuration

class Table(ThreadableDocument):

    """
    Create a table from the specified structure
    """
    MAX_ROWS = 0

    _rows = []
    _columns = []
    _style = None

    @property
    def rows(self):
        """
        Get the rows assigned to this table
        """
        return self._rows

    @accepts(rows=(tuple, list), columns=list, style=(None, str))
    def setup(self, rows, columns, style=None):
        """
        Creates the table

        @param rows list    A list of row data to add
        @param columns list A list of column headings
        @param style string The style to draw the table
        """
        #pylint: disable=arguments-differ
        if isinstance(rows, tuple):
            try:
                self._rows = Table._parse_filter(rows)
                self.threadmanager.append(self._rows)
            #pylint: disable=broad-except
            except Exception as exception:
                Logger().warning('Failed to create filter from config object')
                Logger().warning('Exception was:')
                Logger().warning(exception)
        else:
            self._rows = self._parse_content(rows)

        self._columns = columns
        self._style = style

    @accepts(list)
    def _parse_content(self, rows):
        """
        Parses a list of row/cell data, forming filters where necessary

        @param rows list

        @return list
        """
        for row_index, row in enumerate(rows):
            for cell_index, cell in enumerate(row):
                if isinstance(cell, tuple):
                    try:
                        rows[row_index][cell_index] = Table._parse_filter(cell)
                        self.threadmanager.append(rows[row_index][cell_index])
                    #pylint: disable=broad-except
                    except Exception as exception:
                        Logger().warning('Failed to create filter from config object')
                        Logger().warning('Exception was:')
                        Logger().warning(exception)
        return rows

    @staticmethod
    @accepts(tuple)
    def _parse_filter(cell_content):
        """
        Parses a configuration tuple and forms a filter object

        @param cell_content tuple

        @return Filter
        """
        return Filter(
            cell_content.query,
            max_results=(cell_content.max_results if hasattr(cell_content, 'max_results') else Table.MAX_ROWS),
            fields=(cell_content.fields if hasattr(cell_content, 'fields') else []),
            collate=(cell_content.collate if hasattr(cell_content, 'collate') else None),
            distinct=(cell_content.distinct if hasattr(cell_content, 'distinct') else False),
            namespace=Configuration.NAMESPACE
        )

    def run(self):
        while not self._complete:
            complete = True
            if isinstance(self._rows, Filter):
                self._complete = self._rows.complete
                break
            for row in self._rows:
                for item in row:
                    if isinstance(item, Filter) and item.failed:
                        Logger().warning('Failed to execute \'' + item.query + '\'')
                        Logger().warning('Reason was:')
                        Logger().warning(item.failure)
                    elif isinstance(item, Filter) and not item.complete:
                        complete = False

            if complete:
                self._complete = True

    @accepts(ReportManager)
    def render(self, report):
        """
        Renders the current object into the document

        @param report ReportManager
        """
        Logger().info('Writing table {0}'.format(self.title if self.title is not None else ''))
        if isinstance(self._rows, Filter):
            if len(self._rows.results) == 0:
                Logger().info('Empty table. Skipping...')
                return
            results = self._rows.results
            fields = self._rows.fields
            self._rows = []
            for issue in results:
                self._rows.append([getattr(issue, field.replace(' ', '_').lower()) for field in fields])

        if self.title is not None:
            report.add_heading(Replacements().replace(self.title), 3)

        data = self._rows if isinstance(self._rows, list) else self._rows.results
        for index, row in enumerate(data):
            data[index] = [Replacements().replace(cell) if isinstance(cell, str) else cell for cell in row]

        report.add_table(
            headings=self._columns,
            data=data,
            style=self._style
        )
