"""
Module for using CSV files as a manager
"""

import os
import re
import sys
import importlib
import inspect
import pandas as pd
from releaseessentials.abstract import ManagableAbstract
from releaseessentials.decorators import accepts
from releaseessentials.log import Logger
from releaseessentials.resources import ResultList
from releaseessentials.resources import MultiResultList
from releaseessentials.exceptions import InvalidModuleError

class Csv(ManagableAbstract):
    """
    Takes a CSV file and treats it as a manager object, allowing SQL-like queries to be
    executed on the file(s) to return a specific resultset
    """
    def __init__(self):
        """ Initialise CSV File """
        Logger().info('Initialising CSV interface')

    @property
    def server(self):
        """ Unused server property """
        return None

    @property
    def client(self):
        """
        Lazy load the CSV file object[s]
        """
        self._client = CSVClient(
            self.configuration.csv.input_files,
            datapath=self.configuration.csv.datapath,
            namespace=self.configuration.NAMESPACE
        )
        return self._client

    @accepts(search_query=str, max_results=(bool, int), fields=(None, list))
    def search_issues(self, search_query='', max_results=0, fields=None):
        """
        Search for items in the CSV file[s]

        @param search_query string     What to search for
        @param max_results  [int|bool] If false will return everything
        @param fields       list       A list of fields to include in the results

        @return ResultSet
        """
        results = self.client.search(search_query, max_results=max_results, fields=fields)
        if hasattr(self.configuration.csv, 'combine_results'):
            results.combine = self.configuration.csv.combine_results
        return results

    def projects(self):
        """ Get a list of all files in use within the client """
        # pylint: disable=no-self-use
        return self.configuration.csv.input_files

class CSVClient(list):
    """
    Acts as a client for CSV Files
    """
    _namespace = ''
    _datapath = ''

    @accepts((str, list), namespace=str, datapath=str)
    def __init__(self, input_files, namespace='', datapath=''):
        """
        Create a new client in the current namespace

        @param input_files string|list
        @param namespace   string
        @param datapath    string

        Namespace should be the name of the module containing CSV structures
        to be loaded by the client.

        datapath is the path to load files from.
        """
        self._namespace = namespace
        self._datapath = datapath
        super().__init__()
        if isinstance(input_files, str):
            input_files = [input_files]

        for input_file in input_files:
            self.add_source(input_file)

    @accepts(str)
    def add_source(self, source):
        """
        Add a CSV file as a source to search in

        @param source string A path to a file containing the CSV source
        """
        csvfile = None
        Logger().info('Loading file \'{0}\''.format(source))

        try:
            csvfile = CSVFile(
                os.path.join(self._datapath, source),
                self._get_item(source).DELIMITER,
                self._get_item(source).keys()
            )
            csvfile.load()
            self.append(csvfile)
        except OSError as exception:
            Logger().error('Failed to load file \'{0}\''.format(source))
            Logger().error(exception)
        except ValueError as exception:
            Logger().error('Failed to load file \'{0}\''.format(source))
            Logger().error(exception)

    @accepts(str, max_results=(bool, int), fields=(None, list))
    def search(self, query, max_results=False, fields=None):
        """
        Search the current client for results
        """
        frames = MultiResultList()
        for item in self:
            frame = item.search(
                self._parse_query(query, os.path.basename(item.filename)),
                max_results=max_results,
                fields=fields
            )
            results = ResultList(
                name=os.path.basename(item.filename).split('.')[0].split('/')[-1]
            )
            results.dataframe = frame

            # pylint: disable=unused-variable
            # index is created as part of the tuple extract but isn't required
            for index, series in frame.iterrows():
                results.append(
                    self._get_item(
                        os.path.basename(item.filename)
                    ).from_dict(series.to_dict())
                )
            frames.append(results)
        return frames

    @accepts((str, None), str)
    def _parse_query(self, query, filename):
        """
        Takes the sql-like query and parses it into executable parts

        @param query string
        """
        query = re.subn(r'and', '&', query, flags=re.IGNORECASE)[0]
        query = re.subn(r'or', '|', query, flags=re.IGNORECASE)[0]
        query = CSVClient._replace_operations(query)
        keys = self._get_item(filename).keys()
        for key in keys:
            query = re.subn(key.replace('_', ' '), key, query, flags=re.IGNORECASE)[0]
        return query

    @staticmethod
    def _replace_operations(query):
        """
        Gets the operation being performed as part of a where clause
        """
        operations = [
            (' >= ', [' is greater than or equal to ', ' is not less than ', ' not less than ', ' >= ']),
            (' <= ', [' is less than or equal to ', ' is not greater than ', ' not greater than ', ' <= ']),
            (' != ', [' is not equal to ', ' not equals ', ' != ']),
            (' == ', [' is equal to ', ' equals ', 'equal', ' = ', ' <> ', ' == ']),
            (' > ', [' is less than ', ' less than ', ' < ']),
            (' < ', [' is greater than ', ' greater than ', ' > '])
        ]
        for operator, operation_list in operations:
            for operate in operation_list:
                query = re.subn(operate, operator, query, re.IGNORECASE)[0]
        return query

    @accepts(str)
    def _get_item(self, filename):
        """
        Tries to load a class based on the file extension

        This method looks for a class in releaseessentials.resources with the name of
        <file_extension>FileItem. If it exists, it returns a new instance of it.
        """
        class_name = '{0}FileItem'.format(filename.split('.')[-1].title())
        module_name = str(self._namespace) + '.resources'
        try:
            importlib.import_module(module_name)
            classes = inspect.getmembers(sys.modules[module_name], inspect.isclass)
            return [c for c in classes if c[0] == class_name][0][1]()
        except (IndexError, AttributeError, ImportError):
            raise InvalidModuleError(str(class_name), str(module_name))

class CSVFile(object):
    """
    Thread load a CSV file and return it's contents as a ResultList

    Test bindings:
        csvfile = CSVFile(
            'read count is less than 100 AND chromasone is equal to "chr1" and (
                gene name equals "Xkr4" or gene name equals "gfi1"
            )',
            'samples/GL30_Hd2lox_Hd1.bed',
            fields=['read_count', 'chromasone', 'start', 'end'],
            namespace='releaseessentials'
        )
        csvfile.run()
        csvfile._dataframe.plot(kind='line', x='start', y='end').get_figure().savefig('test.png')
    """
    PRIORITY = 100 # This must have a higher priority than a filter
    _filename = None
    _namespace = None
    _dataframe = None
    _results = None
    _delimiter = ','
    _columns = None

    @accepts(str, str, list)
    def __init__(self, filename, delimiter, columns):
        """
        Set up the CSVFile object
        """
        self._filename = filename
        self._delimiter = delimiter
        self._columns = columns

    @property
    def filename(self):
        """
        Get the filename assigned to this file
        """
        return self._filename

    @property
    def results(self):
        """
        Get the files filtered results as a pandas.Dataframe
        """
        return self._results

    @property
    def dataframe(self):
        """
        Gets the unfiltered CSV contents as a pandas.Dataframe
        """
        return self._dataframe

    def load(self):
        """
        Executes the thread by loading the CSV and performing the query on each line
        coming in. If the line matches, it's loaded.
        """
        self._dataframe = pd.read_csv(
            os.path.join(self._filename),
            delimiter=self._delimiter,
            header=None
        )
        self._dataframe.columns = self._columns

    @accepts(str, max_results=(bool, int), fields=(None, list))
    def search(self, query, max_results=False, fields=None):
        """
        Searches the dataset for items which match the patten given in `query`

        @param query       string
        @param max_results int
        @param fields      list
        """
        query = query if query != '' else None
        self._results = self.dataframe if query is None else self.dataframe.query(query)
        if isinstance(fields, list) and len(fields) != 0:
            self._results = self._results[fields]
        if max_results is not False:
            self._results = self._results.head(max_results)
        return self.results
