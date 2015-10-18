"""
Defines the manager used by the application.

* ProjectManager - loads a project manager api from the managers/subjects directory
* QueryManager
* ThreadManager
"""
import importlib
from weeklyreport.interface import ManagerInterface
from weeklyreport.decorators import accepts
from weeklyreport.configuration import Configuration
from weeklyreport.exceptions import InvalidModuleError
from weeklyreport.exceptions import InvalidClassError
from weeklyreport.helpers import implements

class ProjectManager(object):
    """
    The ProjectManager class acts as a wrapper class to
    load a pluggable back-end interfacing against various
    different agile tracking boards.

    Drivers loaded by this application must implement the
    ManagerInterface interface and be stored in the
    weeklyreport.managers.subjects package.
    """
    __implements__ = (ManagerInterface,)
    _configuration = None
    _client = None

    def __init__(self):
        """
        Initialise the object and call _load
        """
        namespace = self.configuration.NAMESPACE
        self._load(namespace, self.configuration.manager)

    @property
    def client(self):
        """
        Get the loaded manager client
        """
        return self._client

    @property
    def configuration(self):
        """
        Get the cofiguration object
            - load on demand
        """
        if self._configuration is None:
            self._configuration = Configuration()
        return self._configuration

    def projects(self):
        """
        Get a list of projects defined in the agile project manager
        """
        return self._client.projects()

    @accepts(search_query=str, max_results=(bool, int), fields=(None, list))
    def search_issues(self, search_query='', max_results=0, fields=None):
        """
        Search for issues

        @param search_query string     What to search for. When using the default manager, accepts queries in JQL
        @max_results        bool | int If False will load all issues in batches of 50
        @fields             list       A list of fields to retrieve as part of the query results
        """
        return self._client.search_issues(search_query=search_query, max_results=max_results, fields=fields)

    @accepts(str, str)
    def _load(self, namespace, manager):
        """
        Load the requested manager

        @param namespace string The namespace containing the managers ('weeklyreport')
        @param manager   string The name of the manager to load
        """
        try:
            module = importlib.import_module(namespace + '.subjects.' + manager.lower())
        except ImportError:
            raise InvalidModuleError(manager, namespace)
        try:
            name = getattr(module, manager.capitalize())
        except AttributeError:
            raise InvalidClassError(manager.capitalize(), namespace + '.subjects.' + manager.lower())

        if not implements(name, ManagerInterface):
            raise ImportError('{0} must implement \'ManagerInterface\''.format(manager.capitalize()))
        self._client = name()

