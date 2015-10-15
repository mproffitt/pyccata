"""
Contains resource items for mapping <project_manager> results
into ones recognised by the report
"""
from weeklyreport.decorators import accepts

class Issue(object):
    """ Basic storage for a ticket item """

    # pylint: disable=too-many-instance-attributes,too-few-public-methods
    def __init__(self):
        """
        Initialise the Issue object as a struct
        """
        self.key = None
        self.summary = None
        self.issuetype = None
        self.created = None
        self.updated = None
        self.priority = None
        self.description = None
        self.status = None
        self.project = None
        self.fixversions = None
        self.resolution = None
        self.resolutiondate = None
        self.creator = None
        self.assignee = None

class ResultList(list):
    """
    List of results returned by a <project manager>
    """
    _total = 0

    @property
    def total(self):
        """ Get the total number of items returned by the query """
        return self._total

    @total.setter
    @accepts(int)
    def total(self, value):
        """ set the total value """
        self._total = value

    def __init__(self):
        """ Initialise the object """
        super().__init__()

    @accepts(Issue)
    def append(self, item):
        super().append(item)
