"""
LanguageParser is a rudimentary natural language parser for forming SQL-like queries
for use against Pandas dataframe objects.

The language parser takes input as such that:

`my column value is greater than another column value and my column is not equal yet another column`

This would then be parsed and become:

`my_column > another_column & my_column != yet_another_column`
"""
import re
import time
from collections import namedtuple
from itertools import chain
from itertools import combinations
from itertools import permutations
import pandas as pd
import numpy as np

from pyccata.core.decorators import accepts
from pyccata.core.threading import Threadable
from pyupset.resources import ExtractedData

class _Query(object):
    """
    Private class - does the actual parsing
    """
    # pylint: disable=too-few-public-methods
    # Struct type object require only a few methods

    _original = None
    _real = None
    _fields = None

    @accepts(str, list)
    def __init__(self, query, fields):
        """
        Initialise a new _Query item

        @param query string
        @param fields list
        """
        self._original = query
        self._fields = fields
        self._real = self.parse(query)

    @accepts(str)
    def parse(self, query):
        """
        Parse the provided query into an SQL-like query

        @param query string

        This method is expensive to call as it uses a number of regex-matches.
        """
        query = re.subn(r' and ', ' & ', query, flags=re.IGNORECASE)[0]
        query = re.subn(r' or ', ' | ', query, flags=re.IGNORECASE)[0]
        for operator, operation_list in LanguageParser.OPERATIONS:
            for operate in operation_list:
                query = re.subn(operate, operator, query, re.IGNORECASE)[0]

        for field in self._fields:
            query = re.subn(field.replace('_', ' '), field, query, flags=re.IGNORECASE)[0]

        return query

    def __equals__(self, what):
        """
        Is the current item the same as the comparison item?

        Compares string input against the queries stored
        """
        return self._original == what or self._real == what

    def __str__(self):
        """
        String representation of the final query
        """
        return self._real

class _Operator(object):
    """
    Private class for handling operation replacement values
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, operation=None, replacement=None, replaced_in_query=False):
        self.operation = operation
        self.replacement = replacement
        self.replaced_in_query = replaced_in_query

class ExtractedResults(ExtractedData):
    """
    Override class for ExtractedData to allow for extra `query` parameter
    """
    _lock = False
    def __init__(self):
        super().__init__(None, None, None, None)
        self._options = {
            '_in_sets': None,
            '_out_sets': None,
            '_results': None,
            '_filter_config': None,
            '_query': None,
            '_logic': None
        }

    def append_results(self, results):
        """
        Sleep for THREAD_SLEEP then append results
        """
        while ExtractedResults._lock:
            time.sleep(Threadable.THREAD_SLEEP)
        ExtractedResults._lock = True
        # pylint: disable=access-member-before-definition,attribute-defined-outside-init
        # self.results is identified on the parent __getattr__ method
        if self.results is None:
            self.results = pd.DataFrame(results, copy=True).drop_duplicates()
        else:
            self._options['_results'] = self.results.append(results, ignore_index=True).drop_duplicates()
        ExtractedResults._lock = False

    def flatten_results(self, unique_keys):
        """ Takes a multi-frame dataset and flattens it into a single dataframe """
        if not isinstance(unique_keys, list):
            unique_keys = [unique_keys]
        dataframe = None
        for frame in self.in_sets:
            columns = [column for column in self.results.columns if column.endswith(frame)]

            interim = pd.DataFrame(self.results[unique_keys + columns], copy=True)
            interim.columns = unique_keys + [column[:-len('_{0}'.format(frame))] for column in columns]

            if dataframe is None:
                dataframe = pd.DataFrame(interim, copy=True).reset_index(drop=True)
            else:
                dataframe = dataframe.append(interim, ignore_index=True)
        return dataframe.drop_duplicates()

class LanguageParser(object):
    """
    Parse human readable strings into SQL-like queries
    """
    # pylint: disable=too-few-public-methods
    # Not many methods required here
    OPERATIONS = [
        (' >= ', [' is greater than or equal to ', ' is not less than ', ' not less than ', ' >= ']),
        (' <= ', [' is less than or equal to ', ' is not greater than ', ' not greater than ', ' <= ']),
        (' != ', [' is not equal to ', ' not equals ', ' != ']),
        (' == ', [' is equal to ', ' equals ', 'equal', ' = ', ' <> ', ' == ']),
        (' > ', [' is greater than ', ' greater than ', ' > ']),
        (' < ', [' is less than ', ' less than ', ' < '])
    ]

    INVERSIONS = [
        ('>=', '<'), ('<=', '>'),
        ('>', '<'), ('<', '>'),
        ('==', '!='), ('!=', '==')
    ]

    LIMIT_DEFAULT = 200

    _queries = []

    @accepts(str, list)
    def parse(self, query, fields):
        """
        Returns a parsed query

        Loop over all stored queries and return a previously parsed version of
        the query or a new one if the query has not been previously parsed.

        @param query string
        @param fields list
        """
        return str(self[query]) if query in self else self.append(_Query(query, fields))

    def __contains__(self, what):
        for item in self._queries:
            if item == what:
                return True
        return False

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._queries[key]

        for item in self._queries:
            if key == item:
                return item
        raise IndexError('Invalid index {0} for LanguageParser'.format(key))

    def combination(self, query, replacements, fields):
        """
        Loops over the replacements list and creates an instance of the query for each item

        @param query string
        @param replacements list
        @param fields list

        @return list
        """
        queries = []
        for left_name in replacements:
            sections = []
            for right_name in replacements:
                if left_name != right_name:
                    copy = query.replace('_x', '_{0}'.format(left_name))
                    copy = copy.replace('_y', '_{0}'.format(right_name))
                    sections.append(str(self[copy]) if copy in self else self.append(_Query(copy, fields)))
            queries.append('(' + ') | ('.join(sections) + ')')

        return queries

    def combinatorics(self, inclusive_query, exclusive_query, names, limits):
        """
        Loops over the replacements list and creates an instance query for each item

        :param string inclusive_query
        :param string exclusive_query
        :param list   limits
        :param list   names

        Similar to :meth:`LanguageParser.combination`, this method will loop over each item in replacements and create
        a query for each entry.

        The difference here is that for each dataset, an inverse entry will also be written.

        This is such that, for the dataframes::

            dataframe_one
            dataframe_two
            dataframe_three
            dataframe_four

        combinations would be written such that::

            (dataframe_one)
            (dataframe_two)
            (dataframe_three)
            (dataframe_four)
            (dataframe_one, dataframe_two)
            (dataframe_one, dataframe_three)
            (dataframe_one, dataframe_four)
            ...
            (dataframe_one, dataframe_two, dataframe_three, dataframe_four)

        An inverse set would then be provided in the form that "A not in B" giving::

            (dataframe_two, dataframe_three, dataframe_four),
            ...
            (dataframe_three, dataframe_four)
            (dataframe_two, dataframe_four)
            ...

        The query is then re-written such that:

            A == B & A != [C | D] & B != [C | D]

        For this method, it is important that the query does not include hard ranges and in fact value_range is instead
        provided. value_range is a tuple such that ``(value_lower, value_upper)``

        Example::

            query = 'start_x >= (start_y - value_lower) and end_x <= (end_y + value_upper)'

        would be re-written as:

            (dataframe_one, dataframe_two)
            values = (200, 200)
            query = '(start_dataframe_one >= (start_dataframe_two - values[0]) OR (start_dataframe_two >= \
                         (start_dataframe_one - values[0]))) AND \
                         (end_dataframe_one <= (end_end_dataframe_two + values[1]) OR \
                         (end_dataframe_two <= (end_datafrane_one + values[1])))'

        This query is fairly straightforward and the example will bring back all instances where start and end overlap
        by +- 200

        The complexity with pandas arises here in that on a full cartesian product of n-sets, when building a
        combination graph of the data such as those provided by `py-upset`, the data for the combination of
        `dataframe_one` and `dataframe_two` will include data from other set combinations which include one or more of
        these datasets.

        Because pandas does not provide the mechanism to carry out set operations on dataframes, it would be
        incredibly inefficient to attempt to subtract different combination results from each other. Instead it is
        more efficient to limit the amount of data returned for each combination to contain information about other
        sets which explicitly fall outside of the acceptance criteria.

        Therefore in the example, for dataframe_one and dataframe_two, we explicitly include sets which "overlap"
        whilst for `dataframe_three` and `dataframe_four` we exclude these overlaps by explicitly including
        non-overlapping values, then discarding the values within these columns.

        This makes the query considerably more complicated::

            inclusive_query = '(start_dataframe_one >= (start_dataframe_two - 200) OR \
                   (start_dataframe_two >= (start_dataframe_one - 200))) AND \
                   (end_dataframe_one <= (end_end_dataframe_two + 200) OR \
                   (end_dataframe_two <= (end_datafrane_one + 200)))'

            exclusive_queries = [
                '(start_dataframe_one < (start_dataframe_three - 200) OR \
                 (start_dataframe_three < (start_dataframe_one - 200))) AND \
                 (end_dataframe_one > (end_end_dataframe_three + 200) OR \
                 (end_dataframe_three > (end_datafrane_one + 200)))',

                '(start_dataframe_one < (start_dataframe_four - 200) OR \
                 (start_dataframe_four < (start_dataframe_one - 200))) AND \
                 (end_dataframe_one > (end_end_dataframe_four + 200) OR \
                 (end_dataframe_four > (end_datafrane_one + 200)))',

                '(start_dataframe_two < (start_dataframe_three - 200) OR \
                 (start_dataframe_three < (start_dataframe_two - 200))) AND \
                 (end_dataframe_two > (end_end_dataframe_three + 200) OR \
                 (end_dataframe_three > (end_datafrane_two + 200)))',

                '(start_dataframe_two < (start_dataframe_four - 200) OR \
                 (start_dataframe_four < (start_dataframe_two - 200))) AND \
                 (end_dataframe_two > (end_end_dataframe_four + 200) OR \
                 (end_dataframe_four > (end_datafrane_two + 200)))',

                '(start_dataframe_three < (start_dataframe_four - 200) OR \
                 (start_dataframe_four < (start_dataframe_three - 200))) AND \
                 (end_dataframe_three > (end_end_dataframe_four + 200) OR \
                 (end_dataframe_four > (end_datafrane_three + 200)))'
            ]

            query = '(' + inclusive_query + ') AND ~(' + ' AND '.join(exclusive_queries) + ')'

        Combinations containing a single dataframe as the inclusion are excluded from the results when calculating
        combinations in this manner as the values they would contain count as non-overlapping data.
        """
        # pylint: disable=too-many-locals
        # This method is prime for refactoring, however it's complexity means
        # that for now, it's not straight forward. We live with having overcrowding.

        limits = limits._asdict() if limits is not None else {}
        name_combinations = chain.from_iterable(
            combinations(names, i) for i in np.arange(1, len(names) + 1)
        )
        sets = [tuple(frozenset(inset)) for inset in name_combinations]
        queries = []
        query = namedtuple('Query', 'inclusive exclusive')

        for in_sets in sets:
            out_sets = list(set(names) - set(in_sets))

            inclusive_queries = []
            exclusive_queries = []

            start_frame_permutations = [p for p in permutations(list(in_sets))]
            end_frame_permutations = [p for p in permutations(list(out_sets)) if p]

            for current_permutation in start_frame_permutations:
                inclusive_queries.append(
                    self._inclusive_query(inclusive_query, current_permutation, limits)
                )

                # pylint: disable=expression-not-assigned
                # List comprehension result is not required for any reason.
                [
                    exclusive_queries.append(
                        self._inclusive_query(exclusive_query, permutation, limits, left_name=current_permutation[0])
                    )
                    for permutation in end_frame_permutations if end_frame_permutations[0]
                ]

            # pylint: disable=attribute-defined-outside-init
            # Attributes on the ExtractedResults object are initialised through
            # __getattr__ and __setattr methods on the parent `pyupset.resources.ExtractedData` object
            extracted = ExtractedResults()
            extracted.in_sets = in_sets
            extracted.out_sets = out_sets
            extracted.query = query(
                inclusive='(' + ' and '.join(inclusive_queries) + ')',
                exclusive=(
                    '~(' + ' and '.join(exclusive_queries) + ')'
                    if exclusive_queries and exclusive_queries[0] != ''
                    else None
                )
            )
            queries.append(extracted)
        return queries

    @staticmethod
    def _inclusive_query(query, sets, limits, left_name=None):
        """
        Write out and group queries
        """
        queries = []
        sections = []
        if query == '' or query is None:
            return ''

        left_name = sets[0] if left_name is None  else left_name

        left_limit = [
            limit
            for limit in limits
            if left_name.lower().startswith(limit.lower()) or left_name.lower().endswith(limit.lower())
        ][0]

        left_limit = 250
        for right_name in sets:
            if left_name != right_name:
                right_limit = [
                    limit
                    for limit in limits
                    if right_name.lower().startswith(limit.lower()) or right_name.lower().endswith(limit.lower())
                ][0]
                right_limit = left_limit

                copy = query.replace('_x', '_{0}'.format(left_name))
                copy = copy.replace('_y', '_{0}'.format(right_name))
                reversed_copy = query.replace('_x', '_{0}'.format(right_name))
                reversed_copy = reversed_copy.replace('_y', '_{0}'.format(left_name))

                new_query = '(' + copy + ' or ' + reversed_copy + ')'
                new_query = new_query.replace('{left_limit}', str(left_limit))
                new_query = new_query.replace('{right_limit}', str(right_limit))
                sections.append(new_query)

        queries.append('(' + ' and '.join(sections) + ')')
        return '(' + ' and '.join(queries) + ')'

    @accepts(_Query)
    def append(self, query):
        """
        Append a new query to the list and return a string representation of it.

        @param query _Query

        @return string
        """
        self._queries.append(query)
        return str(self._queries[-1])
