"""
Contains helper classes for working within the collation / correlation engine

"""
import math
import time
import pandas as pd
from pyupset import DataExtractor
from pyccata.core.interface import ObservableInterface
from pyccata.core.interface import ResultListItemInterface
from pyccata.core.threading import Threadable
from pyccata.core.managers.thread import ThreadManager
from pyccata.core.exceptions import ThreadFailedError
from pyccata.core.log import Logger

class Partition(object):
    _name = None
    _partitions = None
    _partition_length = 0
    _current_index = 0
    _dataframe = None

    def __init__(self, name, dataframe):
        self._name = name
        self._dataframe = dataframe
        self._partitions = [0]
        self._partition_length = math.ceil(len(dataframe.index) / PartitionRunner.PARTITION_SIZE)
        for i in range(PartitionRunner.PARTITION_SIZE):
            self._partitions.append(self._partitions[-1] + self._partition_length)

    @property
    def name(self):
        return self._name

    def next(self):
        partition_start = self._partitions[self._current_index]
        partition_end = partition_start + self._partition_length
        self._current_index += 1
        return self._dataframe[partition_start:partition_end]

    def reset(self):
        self._current_index = 0

class PartitionRunner(Threadable):
    PRIORITY=1200
    PARTITION_SIZE = 30

    _index = 0
    _query = ''
    _results = None
    _primary_dataset = None
    _partitions = None
    _unique_columns = None
    _running = []
    _mappings = {}
    _extractor = None

    def setup(self, extractor, index, queries, results, primary_dataset, unique_columns):
        self._extractor = extractor
        self._index = index
        self._queries = queries
        self._results = results
        self._names = [item.name for item in results]

        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        short_names = [letter for letter in alphabet[:len(self._results)]]
        self._mappings = {name:short for short, name in zip(short_names, self._names)}

        self._primary_dataset = primary_dataset
        self._unique_columns = unique_columns
        ThreadManager().append(self)

    def merge(self, sets):
        merge = None
        for index, item in enumerate([item['data'] for item in sets]):
            if merge is None:
                merge = item
            else:
                merge = merge.merge(
                    item,
                    on=self._unique_columns,
                    how='outer'
                )
        return merge

    def run(self):
        loop_start = time.clock()
        partitions = []
        for item in self._results:
            partitions.append(
                Partition(item.name, item.dataframe)
            )
            if item.name == self._primary_dataset:
                primary_dataset = partitions[-1]

        index = 0
        while index < self.PARTITION_SIZE:
            merge_sets = []
            combination = ['\033[1m{0}\033[0m'.format(self._mappings[self._primary_dataset])]
            for partition in partitions:
                if partition.name != self._primary_dataset:
                    merge_sets.append({'name': partition.name, 'data': partition.next()})
                    combination.append(self._mappings[partition.name])

            Logger().info(
                'Running data extraction. Index {0} of {1} partitions, (combination: {2}, queries: {3})'.format(
                    index,
                    self.PARTITION_SIZE,
                    ''.join(combination),
                    len(self._queries)
                )
            )

            for x in range(self.PARTITION_SIZE):
                if not self._extractor.add_combination(index, x, combination):
                    continue

                self._running = []
                q_start = time.clock()
                merge_table = self.merge(
                    merge_sets + [{'name': primary_dataset.name, 'data': primary_dataset.next()}]
                )
                m_end = '{0:.2f}'.format(float(time.clock() - q_start))
                Logger().debug(
                    'Combination {0} merge table completed in {1} seconds ({2} rows)'.format(
                        ''.join(combination),
                        m_end,
                        len(merge_table.index)
                    )
                )
                for query in self._queries:
                    self._running.append(
                        DataThreader(merge_table, query, self._unique_columns)
                    )

                self.monitor()
                times = [item.duration for item in self._running]
                Logger().debug(
                    '{4}\n    Combination {0}, Index {5}/{1}, merge_table size: {2}.\n    Average time per query {3}'.format(
                        ''.join(combination),
                        index,
                        len(merge_table.index),
                        times,
                        [len(query.results.index) for query in self._queries],
                        x
                    )
                )
                del times
                del merge_table
                del self._running

            end_time = math.floor(time.clock() - loop_start)
            Logger().info('=========================================================================================')
            Logger().info(
                'Completed partition {0} in {1} seconds. {2} queries, combination: {3}'.format(
                    index,
                    end_time,
                    len(self._queries),
                    ''.join(combination)
                )
            )
            Logger().info('=========================================================================================')
            primary_dataset.reset()
            index += 1

        Logger().info('Completed data extraction')
        self._complete = True

    def monitor(self):
        while True:
            complete = True
            for thread in self._running:
                if not thread.complete:
                    complete = False

                if thread.complete:
                    thread.join()
                elif thread.failed:
                    pass

            if complete:
                break
            time.sleep(Threadable.THREAD_SLEEP)

class DataThreader(Threadable):
    """
    A high priority threading interface for executing searches
    against the merge table inside DataExtraction
    """

    PRIORITY = 1500
    _query = None
    _data = None
    _results = None
    _start_time = 0
    _end_time = 0

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def duration(self):
        return float('{0:.2f}'.format(self.end_time - self.start_time))

    def setup(self, merge_table, query, unique_columns):
        """
        Set up a new data-filter as a threaded object

        :param merge_table: pandas.DataFrame object
        :param query: string
        """
        self._data = merge_table
        self._query = query
        self._unique_columns = unique_columns
        ThreadManager().append(self)

    def run(self):
        """
        Execute filter
        """
        if self._query is None:
            raise ThreadFailedError('No query specified for thread \'{0}\''.format(self.name))

        self._start_time = time.clock()
        results = self._data.query(self._query.query)

        columns = [self._unique_columns]
        for dataframe in self._query.in_sets:
            for column in results.columns:
                if column.endswith(dataframe):
                    columns.append(column)

        self._query.append_results(results[columns])
        del results
        self._end_time = time.clock()
        self._complete = True

class DataExtraction(DataExtractor):
    """
    Override for wrapping combinatorics data
    """

    __implements__ = (ResultListItemInterface,)

    _runners = []
    _combinations = []
    _lock = False

    @property
    def name(self):
        return 'data_extraction_for_' + '_'.join(self.names).lower()

    def add_combination(self, index, secondary, combination):
        while self._lock:
            time.sleep(Threadable.THREAD_SLEEP)
        self._lock = True
        for item in self._combinations:
            if item['index'] == index and item['secondary'] == secondary:
                self._lock = False
                return False
        self._combinations.append({'index': index, 'secondary':secondary, 'combination':combination})
        self._lock = False
        return True

    def search(self, queries, results, unique_columns):
        """
        Wraps the parent merge property inside a thread
        """
        names = [item.name for item in results]
        for index, item in enumerate(results):
            item.dataframe.columns = [
                column
                if column == unique_columns
                else '{0}_{1}'.format(column, names[index])
                for column in item.dataframe.columns
            ]

        for index, item in enumerate(results):
            self._runners.append(
                PartitionRunner(self, index, queries, results, item.name, unique_columns)
            )

    @property
    def complete(self):
        """
        Has the current thread pool completed
        """
        for runner in self._runners:
            if not runner.complete:
                return False
        return True

    def set_results(self, results):
        self._results = results

    def set_sizes(self, sizes):
        self._sizes = sizes

    def keys(self):
        return self.__dict__.keys()
