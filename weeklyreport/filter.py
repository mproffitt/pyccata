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
    # pylint: disable=too-many-instance-attributes
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
    def results(self):
        """ Get the results of the filter search """
        return self._results

    @accepts(str, max_results=(bool, int), fields=list)
    def setup(self, query, max_results=0, fields=list):
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
                    search_query=self._query,
                    max_results=self._max_results,
                    fields=self._fields
                )

            self.notify(False)
            self._complete = True
        except (AssertionError, InvalidQueryError) as exception:
            self.failure = exception

