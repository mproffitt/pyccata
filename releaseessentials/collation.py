"""
Contains all collation methods used as callbacks for releaseessentials.resources.ResultList

@author  Martin Proffitt <mproffitt@jitsc.co.uk>
@link    http://bitbucket.org
@package releaseessentials
"""

from datetime import datetime
from datetime import timedelta
from collections import namedtuple
from releaseessentials.interface import ResultListInterface
from releaseessentials.decorators import accepts

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
    return '{0} days'.format((sum([today - x for x in dates], timedelta(0)) / len(dates)).days)

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
    return '{0} days'.format((sum(dates, timedelta(0)) / len(dates)).days)

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
            result, results.field
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
