"""
Contains all collation methods used as callbacks for pyccata.core.resources.ResultList

@author  Martin Proffitt <mproffitt@jitsc.co.uk>
@link    http://bitbucket.org
@package pyccata.core
"""
import os
import builtins
import time
from datetime import datetime
from datetime import timedelta
from collections import namedtuple
import pandas as pd
import dask.dataframe as dd
from memory_profiler import profile
from pyccata.core.interface import ResultListInterface
from pyccata.core.decorators import accepts
from pyccata.core.helpers import implements
from pyccata.core.parser import LanguageParser
from pyccata.core.extractor import DataExtraction
from pyccata.core.log import Logger
from pyccata.core.threading import Threadable

@accepts(ResultListInterface)
def total_by_field(results):
    """
    Gets the total number of occurances of a given field
    """
    total = []
    for result in results:
        if hasattr(result, results.field) and getattr(result, results.field) is not None:
            total.append(getattr(result, results.field))

    if results.distinct:
        return len(set(total))
    return len(total)

@accepts(ResultListInterface)
def average_days_since_creation(results):
    """
    Gets the average number of days since an issue was created.

    @param field string.
    """
    dates = []
    today = _today
    for result in results:
        dates.append(datetime.strptime(getattr(result, 'created').split('.')[0], '%Y-%m-%dT%H:%M:%S'))
    return '{0} days'.format((builtins.sum([today - x for x in dates], timedelta(0)) / len(dates)).days)

@accepts(ResultListInterface)
def average_duration(results):
    """
    Gets the average duration of a ticket was alive (distance between created and resolved)
    """
    dates = []
    for result in results:
        created = datetime.strptime(getattr(result, 'created').split('.')[0], '%Y-%m-%dT%H:%M:%S')
        resolved = datetime.strptime(getattr(result, 'resolutiondate').split('.')[0], '%Y-%m-%dT%H:%M:%S')
        dates.append(resolved - created)
    return '{0} days'.format((builtins.sum(dates, timedelta(0)) / len(dates)).days)

@accepts(ResultListInterface)
def priority(results):
    """ Gets the number of issues at each prioroty against the current result set """
    levels = [0, 0, 0, 0, 0]
    for result in results:
        try:
            levels[int(result.priority.id) - 1] += 1
        # pylint: disable=bare-except
        # Don't care about any exception here, just skip over if one is thrown
        except:
            pass
    priorities = namedtuple('Priority', 'critical high medium low lowest')
    return priorities(
        critical=levels[0],
        high=levels[1],
        medium=levels[2],
        low=levels[3],
        lowest=levels[4]
    )

@accepts(ResultListInterface)
def flatten(results):
    """ Flattens a list of objects by a field on the object """
    items = [
        item for result in results for item in (getattr(
            result, results.collation.field
        ) if getattr(result, results.field) is not None else [])
    ]
    if results.distinct:
        return sorted(list(set(items)))
    return items

def _today():
    """
    Private wrapper for datetime.today for testing
    """
    return datetime.today()

def sum_total(results, collation):
    """
    Provides a total sum of columns across all datasets in a MultiResultList
    """
    total = 0
    return_results = False

    data = {collation.field: {}, 'name': {}}
    index = 0
    for item in results:
        if implements(item, ResultListInterface):
            if return_results is False:
                return_results = type(item)(
                    name='_'.join([name.name for name in results])
                )

                # pylint: disable=protected-access
                return_results._name = '_'.join([name.name for name in results])
            data[collation.field][index] = item.dataframe.sum(axis=0)[collation.field]
            data['name'][index] = item.name
            index += 1
        else:
            total += (getattr(item, results.field) if hasattr(item, results.field) else 0)

    if return_results is not False:
        return_results.dataframe = pd.DataFrame.from_records(data)
        return return_results
    return total

def sum_outer(results, collation):
    """
    Performs a sum on the columns along with an outer join on multiple result
    sets. Missing values are filled with 'unknown'
    """
    group_by = results.group_by
    names = [item.name for item in results]
    columns = ['{0}_{1}'.format(collation.field, item.name) for item in results]

    return_results = type(results[0])(name='_'.join([name.name for name in results]))
    # pylint: disable=protected-access
    return_results._group_by = results.group_by
    return_results._field = collation.field

    results = [item.dataframe.groupby(results.group_by, as_index=False).sum() for item in results]
    data = None
    for index, dataframe in enumerate(results):
        if index == 0:
            data = dataframe
        else:
            data = data.merge(
                dataframe,
                on=group_by,
                suffixes=('_{0}'.format(names[index-1]), '_{0}'.format(names[index])),
                how='outer'
            )
            data.fillna(0, inplace=True)
    return_results.dataframe = pd.DataFrame(data.sort_values(columns, ascending=True))
    return_results.group_by = group_by
    return return_results

def _merge(results, collation):
    """
    Carry out a full outer merge on n dataframes
    """
    data = None
    names = [item.name for item in results]
    results = [dd.dataframe(item.dataframe, npartitions=collation.partitions) for item in results]

    Logger().info('Creating merge table')
    merge_start = time.clock()
    for index, item in enumerate(results):
        columns = [
            column
            if column == collation.join.column
            else '{0}_{1}'.format(column, names[index])
            for column in item.columns
        ]
        item.columns = columns
        if index == 0:
            data = item
        else:
            suffixes = (
                '_{0}'.format(names[index-1]),
                '_{0}'.format(names[index])
            )
            data = data.merge(
                item,
                on=collation.join.column,
                how=collation.join.method,
                suffixes=suffixes,
                copy=False
            )
    Logger().info(
        'Merge table created in {0} seconds. ({1} rows)'.format(
            time.clock() - merge_start,
            len(data.index)
        )
    )
    return data

@profile
def subquery(results, collation):
    """
    Perform a sub-query on the provided resultset

    @param results MultiResultList
    @param collation Collation

    Note. This method creates a full outer join on the datasets passed in before performing the query.

    This can then cause Pandas to fail with a memory error on medium sized datasets.
    """
    names = [item.name for item in results]
    return_results = results
    mapping_item = results[0].type()
    compiled_query = '(' + ') | ('.join(
        LanguageParser().combination(
            collation.query, names, mapping_item().keys()
        )
    ) + ')'

    return_results.name = names
    return_results.dataframe = _merge(results, collation).query(compiled_query)
    return_results.dataframe.to_csv(os.path.join(collation.output_dir, 'overlaps.csv'), index=False)

    return return_results

# pylint: disable=anomalous-backslash-in-string
# Docblock contains a TeX equation.
def combinatorics(results, collation):
    """
    Creates combination results between datasets based on the equation:

    ```
    g = 50
    \par
    D = [d_1 ... d_n]
    \par
    l(x): x[start] - 200
    \par
    u(x): x[end] + 200
    \par
    \
    \par
    R = \left [\forall d \in D: X_i = d \times \prod_{i \in [D - d]}D \Rightarrow (
        \forall p \in x[
            y = (z- \lceil{\left |s \right |\over g}\rceil):
            z = (y+ \lceil{\left |s \right |\over g}\rceil)
        ]: \forall x \in X
    ):
        \left [x_s \cap x_{i \in[D-d]} \because (
            l(x_d) \geq l(x_{i \in [D-d]}) \land u(x_d) \leq u(x_{i \in [D-d]})
        ) - (
            l(x_d) \gnsim l(x_{i \in [D-d]}) \land u(x_d) \lnsim u(x_{i \in [D-d]})
        )\right ]
    \right ]
    ```

    :inputs:

        {
            "inclusive_query": "",
            "exclusive_query": ""
        }
    """
    method_start = time.clock()
    parser = LanguageParser()
    extractor = DataExtraction(unique_keys=collation.join.column)
    sizes = {}
    for item in results:
        sizes[item.name] = len(item)
    extractor.set_sizes(sizes)
    extractor.names = [item.name for item in results]

    queries = parser.combinatorics(
        collation.query.inclusive,
        collation.query.exclusive,
        extractor.names,
        collation.limits
    )

    extractor.search(queries, results, collation.join.column)
    while not extractor.complete:
        time.sleep(Threadable.THREAD_SLEEP)
    extractor.set_results(queries, collation.join.column)

    Logger().info('Collation completed in {0} seconds'.format((time.clock() - method_start)))
    results.dataframe = (extractor, None)
    return extractor
