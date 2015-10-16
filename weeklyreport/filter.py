"""
The filter module provides a hierarchy of objects for
searching the ProjectManager depending on the search type
being required for a document section.

At the top level of these is the observable Filter object.
"""
from weeklyreport.interface import ObservableInterface
from weeklyreport.decorators import accepts
from weeklyreport.threading import Threadable
from weeklyreport.manager import ProjectManager
from weeklyreport.resources import ResultList
from weeklyreport.exceptions import InvalidQueryError

class Filter(Threadable):
    """
    The Filter object provides a base class for all filters
    requested by the application.
    """
    # pylint: disable=too-many-instance-attributes,too-many-public-methods
    # It is understood that this class requires a number of attributes and
    # accessor methods.
    __implements__ = (ObservableInterface,)

    _query = None
    _fields = None
    _results = None
    _observers = None
    _max_results = None
    _projectmanager = None

    @property
    def projectmanager(self):
        """ get the project manager assigned to this filter """
        return self._projectmanager

    @projectmanager.setter
    @accepts(ProjectManager)
    def projectmanager(self, manager):
        """ assign a project manager to the filter """
        self._projectmanager = manager

    @property
    def query(self):
        """ Get the query defined within this object """
        return self._query

    @property
    def fields(self):
        """ Get a list of fields to restrict the search to """
        return self._fields

    @property
    def max_results(self):
        """ Get the max results returned by this filter """
        return self._max_results

    @property
    def results(self):
        """ Get the results of the filter search """
        return self._results

    @accepts(str, max_results=(bool, int), fields=(None, list))
    def setup(self, query, max_results=0, fields=None):
        """
        Initialise the filter

        @param query       string     The query to search with
        @param max_results [bool|int] If False will retrieve all matching issues
                                         in batches of 50
        @param fields      list       An optional list of fields to retrieve.
                                         If empty, retrieves all fields
        """
        # pylint: disable=arguments-differ
        # It is understood that the arguments will always differ
        # from the super() class on this method due to the use of
        # *args and **kwargs in the call from __init__
        self._query = query
        self._fields = fields
        self._observers = []
        self._max_results = max_results
        self._results = None

    @accepts(ObservableInterface)
    def append(self, item):
        """ Append an observer to the list of observables """
        self._observers.append(item)

    @accepts((bool, ResultList))
    def notify(self, results):
        """ notify observers or store results """
        if not results:
            for observer in self._observers:
                observer.notify(self.results)
        else:
            self._results = results
            self._complete = True

    def run(self):
        """
        Triggers the current thread and any child threads (if defined)

        The status of this thread can then be monitored via the
        ``Filter::complete`` property.
        """
        try:
            assert self.projectmanager is not None
            if not self._complete:
                self._results = self.projectmanager.search_issues(
                    search_query=self.query,
                    max_results=self.max_results,
                    fields=self.fields
                )

            self.notify(False)
            self._complete = True
        except (AssertionError, InvalidQueryError) as exception:
            self.failure = exception

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

