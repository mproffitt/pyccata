"""
The filter module provides a hierarchy of objects for
searching the ProjectManager depending on the search type
being required for a document section.

At the top level of these is the observable Filter object.
"""
from weeklyreport.interface import ObservableInterface
from weeklyreport.decorators import accepts
from weeklyreport.threading import Threadable
from weeklyreport.managers.project import ProjectManager
from weeklyreport.resources import ResultList

class Filter(Threadable):
    """
    The Filter object provides a base class for all filters
    requested by the application.
    """
    # pylint: disable=too-many-instance-attributes,too-many-public-methods
    # It is understood that this class requires a number of attributes and
    # accessor methods.
    __implements__ = (ObservableInterface,)
    PRIORITY = 1000

    _query = None
    _fields = None
    _results = None
    _observers = None
    _max_results = None
    _projectmanager = None
    _observing = False

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

    @property
    def hasobservers(self):
        """ returns True if the number of items observing this one is > 0 """
        return len(self._observers) > 0

    @property
    def observing(self):
        """ Is this item being observed? """
        return self._observing

    @observing.setter
    @accepts(bool)
    def observing(self, value):
        """ Tell the item that it is being observed """
        self._observing = value

    @property
    def observers(self):
        """ get the list of observers to this object """
        return self._observers

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
        item.observing = True
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
        # pylint: disable=broad-except
        # It is necessary to have a broad exception case here
        # as we need to set the failure state of the thread
        # regardless of what type of exception is thrown
        except Exception as exception:
            self.failure = exception

