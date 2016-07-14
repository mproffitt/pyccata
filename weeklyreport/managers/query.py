"""
Query Manager
"""
from weeklyreport.filter import Filter
from weeklyreport.decorators import accepts

class QueryManager(list):
    """
    The QueryManager accepts filters as they are loaded
    and stores them in a list.

    As new queries come in, the manager scans the list to
    see if an existing query has already been provided which
    matches its criteria.

    If it has, the query is appended to the observers of the
    earlier query which assigns its results via the notify.

    Filters provided to the QueryManager must implement
    Observable for this manager to understand.

    TODO:
      * Implement remove methods.
        At present when an item is removed from the queue, any
        observing items are also removed. This can be dangerous
        and instead, when an item is removed, any observing items
        should be returned to the bottom of the queue with
        subsequent items monitoring the first observer to be removed.
    """

    @accepts(Filter)
    def append(self, item):
        """
        Append a Filter item to the Query queue.

        The query manager only deals with Filter items.
        """
        observed = False
        for query in self:
            if (query.query == item.query
                    and query.max_results == item.max_results
                    and query.fields == item.fields):
                query.append(item)
                observed = True
                break
        if not observed:
            super().append(item)
