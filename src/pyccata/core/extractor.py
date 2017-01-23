"""
Contains helper classes for working within the collation / correlation engine

"""
import os
import math
import time
import psutil
import numpy as np
from pyupset import DataExtractor
from pyccata.core.interface import ResultListItemInterface
from pyccata.core.threading import Threadable
from pyccata.core.managers.thread import ThreadManager
from pyccata.core.exceptions import ThreadFailedError
from pyccata.core.log import Logger
from pyccata.core.configuration import Configuration

class PartitionSet(object):
    """
    A partition set contains a left dataframe, a right dataframe and the results of
    searching within that dataframe
    """
    _left = None
    _right = None

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    def __init__(self, left_frame, right_frame):
        self._left = left_frame
        self._right = right_frame


class Partition(object):
    """
    Given a pandas dataframe, will split the index into n parts of size x
    where x is defined by |df| / n
    """
    _name = None
    _partitions = None
    _partition_length = 0
    _current_index = 0
    _dataframe = None

    def __init__(self, name, dataframe, partition_size):
        self._name = name
        self._dataframe = dataframe
        self._partitions = [0]
        self._partition_length = math.ceil(len(dataframe.index) / partition_size)
        for _ in range(partition_size):
            self._partitions.append(self._partitions[-1] + self._partition_length)

    @property
    def name(self):
        """
        Gets the name of the partition
        """
        return self._name

    def next(self):
        """
        Gets the next partition in the list
        """
        partition_start = self._partitions[self._current_index]
        partition_end = partition_start + self._partition_length
        self._current_index += 1
        return self._dataframe[partition_start:partition_end]

    def reset(self):
        """
        Resets the partition index back to 0
        """
        self._current_index = 0

class PartitionRunner(Threadable):
    """
    Runs a set of queries over a partition

    When a merge is carried out, to avoid differences in cartesian products
    whereby AxB is not always the same as BxA, this class re-arranges the merge
    for each set in results as primary
    """
    # pylint: disable=too-many-instance-attributes
    PRIORITY = 1200
    PARTITION_SIZE = 1
    MAX_THRESHOLD = 16

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
        """
        Set up the partition runner

        :param pyccata.core.classes.DataExtraction: extractor
        :param int: index
        :param list: queries
        :param list: results
        :param string: primary_dataset
        :param list|string: unique_columns

        queries is a list of ``pyccata.core.parser.ExtractedResults`` objects
        results is a list of ``pandas.DataFrame`` objects
        primary_dataset dictates which frame to use for the left side of the join
        unique_columns determines which column to use for the join
        """
        # pylint: disable=arguments-differ,too-many-arguments
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

    @staticmethod
    def merge_size(left_frame, right_frame, group_by, how='inner'):
        """
        Determine the size of a merge between two pandas dataframes.

        :param pandas.DataFrame: left_frame
        :param pandas.DataFrame: right_frame
        :param string: group_by the key to merge the frames on
        :param string: how How to carry out the merge (left, right, inner, outer). Default outer.

        :return: int
        """
        # pylint: disable=too-many-locals
        # This method is always going to be a beast until the upstream implementation is complete.
        # @see https://github.com/pandas-dev/pandas/issues/15068
        left_groups = left_frame.groupby(group_by).size()
        right_groups = right_frame.groupby(group_by).size()
        left_keys = set(left_groups.index)
        right_keys = set(right_groups.index)
        intersection = right_keys & left_keys
        left_diff = left_keys - intersection
        right_diff = right_keys - intersection

        left_nan = len(left_frame[left_frame[group_by] != left_frame[group_by]])
        right_nan = len(right_frame[right_frame[group_by] != right_frame[group_by]])
        left_nan = 1 if left_nan == 0 and right_nan != 0 else left_nan
        right_nan = 1 if right_nan == 0 and left_nan != 0 else right_nan

        sizes = [(left_groups[group_name] * right_groups[group_name]) for group_name in intersection]
        sizes += [left_nan * right_nan]

        left_size = [left_groups[group_name] for group_name in left_diff]
        right_size = [right_groups[group_name] for group_name in right_diff]
        if how == 'inner':
            return sum(sizes)
        elif how == 'left':
            return sum(sizes + left_size)
        elif how == 'right':
            return sum(sizes + right_size)
        return sum(sizes + left_size + right_size)

    @staticmethod
    def mem_fit(left, right, key, how='inner'):
        """
        Determine if a merge between dataframes 1 and 2 will fit in memory

        :param pandas.DataFrame: left
        :param pandas.DataFrame: right
        :param string: key The key on which to merge
        :param string: how How to carry out the merge (left, right, inner, outer). Default outer.

        :returns: bool
        """
        rows = PartitionRunner.merge_size(left, right, key, how)
        cols = len(right.columns) + (len(right.columns) - 1)
        required_memory = (rows * cols) * np.dtype(np.float64).itemsize
        return required_memory <= psutil.virtual_memory().available

    @staticmethod
    def slices(left, right, key, how='inner'):
        """
        Computes the number of partitions required to efficiently compute overlaps between datasets.

        :param pandas.DataFrame: left
        :param pandas.DataFrame: right
        :param string: key
        :param string: how [default=inner]

        :return int:
        """
        threshold = (((psutil.virtual_memory().available / 1024 ) / 1024) / 1024) // self.MAX_THRESHOLD
        slices = 1
        memory = 0
        while True:
            q1_slice = q1[:len(q1.index) // slices]
            q2_slice = q2[:len(q2.index) // slices]
            rows = PartitionRunner.merge_size(q1_slice, q2_slice, 'chromosome', how='outer')
            memory = ((((rows * cols * np.dtype(np.float64).itemsize) / 1024) / 1024) / 1024)
            if memory < threshold:
                break
            slices += 1

        return slices

    def merge(self, sets):
        """
        Generate an outer join between two dataframes
        """
        merge = None
        for _, item in enumerate([item['data'] for item in sets]):
            if merge is None:
                merge = item
            else:
                Logger().info(
                    'Partition size = {0}'.format(
                        PartitionRunner.merge_size(merge, item, how='outer', group_by=self._unique_columns)
                    )
                )

                merge = merge.merge(
                    item,
                    on=self._unique_columns,
                    how='outer'
                )
        return merge

    def run(self):
        """
        Run the quries over the merge table inside a thread
        """
        # pylint: disable=too-many-locals
        loop_start = time.clock()
        partitions = []
        for item in self._results:
            partitions.append(
                Partition(item.name, item.dataframe, self.PARTITION_SIZE)
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

            for size in range(self.PARTITION_SIZE):
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
                message = '{4}\n    Combination {0}, Index {5}/{1}'
                message += ', merge_table size: {2}.\n    Average time per query {3}'
                Logger().debug(
                    message.format(
                        ''.join(combination),
                        index,
                        len(merge_table.index),
                        times,
                        [len(query.results.index) for query in self._queries],
                        size
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
        """
        Wait for all child threads to complete
        """
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
        """
        Get the start time of the data threader
        """
        return self._start_time

    @property
    def end_time(self):
        """
        Get the end time of the data threader run
        """
        return self._end_time

    @property
    def duration(self):
        """
        Get the duration of the datathreader as a 2 decimal float
        """
        return float('{0:.2f}'.format(self.end_time - self.start_time))

    def setup(self, merge_table, query, unique_columns):
        """
        Set up a new data-filter as a threaded object

        :param merge_table: pandas.DataFrame object
        :param query: string
        """
        # pylint: disable=arguments-differ

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
        interim = self._data.query(self._query.query.inclusive)
        results = interim if self._query.query.exclusive is None else interim.query(self._query.query.exclusive)

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
        """
        Get the name to use for the graph
        """
        return 'data_extraction_for_' + '_'.join(self.names).lower()

    @property
    def primary_set_length(self):
        """
        Get the length of the primary data-set
        """
        return sum([1 for item in self._results if len(item.in_sets) == 1])

    def add_combination(self, index, secondary, combination):
        """
        Add a combination to the extraction
        """
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

    def set_results(self, results, unique_keys):
        """
        Set the results of the extraction
        """
        self._results = results
        self._compute_logic()

        for _, query in enumerate(self._results):

            flat = query.flatten_results(unique_keys)
            filename = 'flattened_{0}.csv'.format('_'.join(sorted(query.in_sets)))
            flat.to_csv(
                os.path.join(
                    Configuration().csv.output_directory,
                    '{0}'.format(filename)
                ),
                sep='\t'
            )

    def as_logic(self):
        """
        Gets the results of the extraction as a dataframe logic set

        :returns: dictionary where the key is the logic.

        ```
        {
            '0001': {
                'count': int,
                'name': string
            }
        }
        ```
        """
        result_dict = {}
        for item in self._results:
            result_dict[item.logic] = {
                'count': len(item.results),
                'name': item.in_sets[0] if len(item.in_sets) == 1 else None
            }
        return result_dict

    def set_sizes(self, sizes):
        """
        Set the sizes of each set
        """
        self._sizes = sizes

    def keys(self):
        """
        Get the keys used for data extraction
        """
        return self.__dict__.keys()

    def _compute_logic(self):
        """
        Compute the logic used to order the sets for displaying as a venn diagram.

        When sets are computed, the order they appear in cannot be determined against the
        location they belong in on a venn diagram.

        This is overcome by applying a binary order against them.

        To achieve this, we take each of the initial base sets (with only 1 set) and assign a binary
        position against it, such that:

        set 1: 0001
        set 2: 0010
        set 3: 0100
        set 4: 1000

        Intersection sets are then calculated such that:

        set 1 & set 2: 0011
        set 1 & set 3: 0101
        set 1 & set 4: 1001
        set 2 & set 3: 0110
        set 2 & set 4: 1010
        set 3 & set 4: 1100
        set 1 & set 2 & set 3 & set 4: 1111
        """
        set_length = self.primary_set_length
        for index, item in enumerate(self._results):
            if len(item.in_sets) == 1:
                logic = '1' + ''.join(['0' for _ in range(index)])
                item.logic = logic.zfill(set_length)

        for item in self._results:
            if len(item.in_sets) > 1:
                computed_logic = 0
                for name in item.in_sets:
                    computed_logic += int(
                        [query.logic
                         for query in self._results if len(query.in_sets) == 1 and query.in_sets[0] == name
                        ][0], 2
                    )
                item.logic = bin(computed_logic).split('0b')[-1].zfill(set_length)
