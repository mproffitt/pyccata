"""
Module for using CSV files as a manager
"""

import os
from time import sleep
import pandas as pd
from pyccata.core.abstract import ManagableAbstract
from pyccata.core.decorators import accepts
from pyccata.core.log import Logger
from pyccata.core.resources import ResultList
from pyccata.core.resources import MultiResultList
from pyccata.core.threading import Threadable
from pyccata.core.exceptions import ThreadNotStartedError
from pyccata.core.language_parser import LanguageParser
from pyccata.core.helpers import resource

class Csv(ManagableAbstract):
    """
    Takes a CSV file and treats it as a manager object, allowing SQL-like queries to be
    executed on the file(s) to return a specific resultset
    """

    REQUIRED = [
        'datapath',
        'input_files',
        'output_directory'
    ]

    def __init__(self):
        """ Initialise CSV File """
        Logger().info('Initialising CSV interface')

    @property
    def server(self):
        """ Unused server property """
        return None

    @property
    def threadmanager(self):
        """
        Gets the assigned threadmanager from the client

        @return ThreadManager
        """
        return self.client.threadmanager

    @threadmanager.setter
    def threadmanager(self, threadmanager):
        """
        Assigns the threadmanager to the client
        """
        self.client.threadmanager = threadmanager

    @property
    def client(self):
        """
        Get the assigned client for this manager
        """

        namespace = (
            self.configuration.csv.namespace
            if hasattr(self.configuration.csv, 'namespace')
            else self.configuration.NAMESPACE
        )
        if not self._client or self._client is None:
            self._client = CSVClient(
                self.configuration.csv.input_files,
                datapath=self.configuration.csv.datapath,
                namespace=namespace
            )
        return self._client

    @accepts(search_query=str, max_results=(bool, int), fields=(None, list), group_by=(None, str))
    def search_issues(self, search_query='', max_results=0, fields=None, group_by=None):
        """
        Search for items in the CSV file[s]

        @param search_query string     What to search for
        @param max_results  [int|bool] If false will return everything
        @param fields       list       A list of fields to include in the results

        @return ResultSet
        """
        results = self.client.search(search_query, max_results=max_results, fields=fields, group_by=group_by)
        if hasattr(self.configuration.csv, 'combine_results'):
            results.combine = self.configuration.csv.combine_results
        return results

    def projects(self):
        """ Get a list of all files in use within the client """
        # pylint: disable=no-self-use
        return self.configuration.csv.input_files

class CSVFile(Threadable):
    """
    Thread load a CSV file and return it's contents as a ResultList

    Test bindings:
        csvfile = CSVFile(
            'read count is less than 100 AND chromasone is equal to "chr1" and (
                gene name equals "Xkr4" or gene name equals "gfi1"
            )',
            'samples/GL30_Hd2lox_Hd1.bed',
            fields=['read_count', 'chromasone', 'start', 'end'],
            namespace='pyccata.core'
        )
        csvfile.run()
        csvfile._dataframe.plot(kind='line', x='start', y='end').get_figure().savefig('test.png')
    """
    PRIORITY = 1001 # This must have a higher priority than a filter
    _filename = None
    _namespace = None
    _dataframe = None
    _delimiter = ','
    _columns = None

    added = False

    @accepts(str, str, list)
    def setup(self, filename, delimiter, columns):
        """
        Set up the CSVFile object
        """
        # pylint: disable=arguments-differ
        # Parent method is *args **kwargs
        self._filename = filename
        assert os.stat(self.filename).st_size > 0

        self._delimiter = delimiter
        self._columns = columns

    @property
    def filename(self):
        """
        Get the filename assigned to this file
        """
        return self._filename

    @property
    def dataframe(self):
        """
        Gets the unfiltered CSV contents as a pandas.Dataframe
        """
        return self._dataframe

    def run(self):
        """
        Loads the CSV file in a separate thread
        """
        Logger().info('Loading file \'{0}\''.format(self._filename))
        try:
            self._dataframe = pd.read_csv(
                self._filename,
                delimiter=self._delimiter,
                header=None
            )
            self._dataframe.columns = self._columns
            self._complete = True
        # pylint: disable=broad-except
        # Any failure of the thread should be trapped and assigned to thread-failure state
        except Exception as exception:
            self.failure = exception

    @accepts(str, max_results=(bool, int), fields=(None, list), group_by=(None, str))
    def search(self, query, max_results=False, fields=None, group_by=None):
        """
        Searches the dataset for items which match the patten given in `query`

        @param query       string
        @param max_results int
        @param fields      list
        """
        if self.dataframe is None:
            raise ThreadNotStartedError('Waiting for dataframe to load')
        query = query if query != '' else None

        Logger().info('Executing query "{0}" on file "{1}"'.format(query, self._filename))
        results = self.dataframe if query is None else self.dataframe.query(query)
        Logger().debug('Got {0} results for query {1}'.format(len(results), query))

        if isinstance(fields, list) and len(fields) != 0:
            results = results[fields]
        if max_results is not False:
            results = results.head(max_results)
        if group_by is not None:
            results.groupby(group_by)
        Logger().debug('Done for query "{0}" on file "{1}"'.format(query, self._filename))
        return results

class CSVClient(list):
    """
    Acts as a client for CSV Files
    """
    _namespace = ''
    _datapath = ''
    _input_files = None
    _threadmanager = None
    _language_parser = None

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
        self._language_parser = LanguageParser()

        super().__init__()
        if isinstance(input_files, str):
            input_files = [input_files]
        self._input_files = input_files


    def _load(self):
        """
        Load all files assigned to this client
        """
        for input_file in self._input_files:
            self.add_source(input_file)

    @property
    def threadmanager(self):
        """
        Gets the threadmanager assigned into this client

        @return ThreadManager
        """
        return self._threadmanager

    @threadmanager.setter
    def threadmanager(self, threadmanager):
        """
        Set the threadmanager for this client

        The thread manager is injected via the ThreadManager class
        at point of creation.

        Once assigned, the client will then load all assigned files.
        """
        self._threadmanager = threadmanager
        self._load()

    @accepts(CSVFile)
    def append(self, item):
        """
        Appends a CSV file to the client
        """
        assert self.threadmanager is not None
        self.threadmanager.append(item)
        super().append(item)

    @accepts(str)
    def add_source(self, source):
        """
        Add a CSV file as a source to search in

        @param source string A path to a file containing the CSV source
        """
        csvfile = None
        try:
            csvfile = CSVFile(
                os.path.join(self._datapath, source),
                self._get_item(source).DELIMITER,
                self._get_item(source).keys()
            )
            self.append(csvfile)
        except (OSError, ValueError) as exception:
            Logger().error('Failed to load file \'{0}\''.format(source))
            Logger().error(exception)

    def clear(self):
        for item in self:
            item.added = False

    @accepts(str, max_results=(bool, int), fields=(None, list), group_by=(None, str))
    def search(self, query, max_results=False, fields=None, group_by=None):
        """
        Search the current client for results
        """
        self._wait_for_load()
        frames = MultiResultList()
        for item in self:
            frame = item.search(
                self._language_parser.parse(
                    query,
                    self._get_item(
                        os.path.basename(item.filename)
                    ).keys()
                ),
                max_results=max_results,
                fields=fields,
                group_by=group_by
            )

            results = ResultList(
                name=os.path.basename(item.filename).split('.')[0].split('/')[-1]
            )
            results.dataframe = (frame, self._get_item(os.path.basename(item.filename)))
            frames.append(results)

        return frames

    def _wait_for_load(self):
        """
        Pauses the client until all child threads have completed
        """
        Logger().debug('Waiting for CSV client items to load')
        while True:
            complete = True
            for item in self:
                complete = item.complete
                if not complete:
                    break

            if complete:
                break
            sleep(Threadable.THREAD_SLEEP)
        Logger().info('Done loading CSV client')

    @accepts(str)
    def _get_item(self, filename):
        """
        Tries to load a class based on the file extension

        This method looks for a class in pyccata.core.resources with the name of
        <file_extension>FileItem. If it exists, it returns a new instance of it.
        """
        class_name = '{0}FileItem'.format(filename.split('.')[-1].title())
        return resource(class_name, self._namespace)()
