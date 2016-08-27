"""
Contains the structure for creating tables
"""

from pyccata.core.managers.report import ReportManager
from pyccata.core.abstract import ThreadableDocument
from pyccata.core.decorators import accepts
from pyccata.core.filter import Filter
from pyccata.core.log import Logger

from pyccata.core.resources import MultiResultList
from pyccata.core.resources import Replacements
from pyccata.core.configuration import Configuration

class Table(ThreadableDocument):

    """
    Create a table from the specified structure
    """
    MAX_ROWS = 0

    _rows = []
    _columns = []
    _style = None
    _report = None

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
            group_by=(cell_content.group_by if hasattr(cell_content, 'group_by') else None),
            namespace=Configuration.NAMESPACE
        )

    def run(self):
        while not self._complete:
            complete = True
            if isinstance(self._rows, Filter):
                self._complete = self._rows.complete
                continue
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
        self._report = report
        Logger().info('Writing table {0}'.format(self.title if self.title is not None else ''))
        if isinstance(self._rows, Filter):
            if len(self._rows.results) == 0:
                Logger().info('Empty table. Skipping...')
                return
            results = self._rows.results
            if self._columns is None or len(self._columns) == 0:
                self._columns = list(results.columns)
            if isinstance(results, MultiResultList):
                if not results.combine:
                    return self._write_multi(results)
                results = [item for result in results for item in result]

            if hasattr(self._rows.results, 'dataframe') and self._rows.results.dataframe is None:
                fields = self._rows.fields
                self._rows = []
                for issue in results:
                    self._rows.append([getattr(issue, field.replace(' ', '_').lower()) for field in fields])

        if self.title is not None:
            self._write_heading()
        self._write_table(self._rows)

    def _write_heading(self, alternate_title=''):
        """
        Writes a heading for the table

        @param alternate_title string An optional title to use in place
        """

        level = 3 if alternate_title == '' else 4
        title = self.title if alternate_title == '' else alternate_title
        self._report.add_heading(Replacements().replace(title), level)

    @accepts(MultiResultList)
    def _write_multi(self, results):
        """
        Writes a set of ResultList items in individual tables

        @param results MultiResultList
        """
        fields = self._rows.fields
        for resultset in results:
            rows = []
            for issue in resultset:
                if isinstance(issue, dict):
                    issue = resultset.from_dict(issue)
                rows.append([getattr(issue, field.replace(' ', '_').lower()) for field in fields])
            self._write_heading(resultset.name if hasattr(resultset, 'name') else '')
            self._write_table(rows)

    def _write_table(self, results):
        """
        Write out a set of results as a table
        """
        data = results if isinstance(results, list) else results.results
        if hasattr(data, 'dataframe') and data.dataframe is None:
            for index, row in enumerate(data):
                data[index] = [Replacements().replace(cell) if isinstance(cell, str) else cell for cell in row]

        if len(data) > Table.MAX_ROWS and (hasattr(data, 'dataframe') and data.dataframe is not None):
            data.dataframe.to_csv(results.name + '.csv', index=False)
            self._report.add_paragraph('Table results written to file \'{0}\''.format(results.name + '.csv'))
        else:
            self._report.add_table(
                headings=self._columns,
                data=data,
                style=self._style
            )
