"""
Defines the manager used by the application.

* ProjectManager - loads a project manager api from the managers/clients directory
* QueryManager
* ThreadManager
"""
from pyccata.core.interface import ManagerInterface
from pyccata.core.manager import Manager
from pyccata.core.decorators import accepts
from pyccata.core.log import Logger

class ProjectManager(Manager):
    """
    The ProjectManager class acts as a wrapper class to
    load a pluggable back-end interfacing against various
    different agile tracking boards.

    Drivers loaded by this application must implement the
    ManagerInterface interface and be stored in the
    pyccata.core.managers.clients package.
    """
    __implements__ = (ManagerInterface,)

    def __init__(self):
        """
        Initialise the object and call _load
        """
        namespace = self.configuration.NAMESPACE
        self._load(namespace, self.configuration.manager, must_implement=ManagerInterface)
        #ProjectManager.REQUIRED = self.client.REQUIRED

    @property
    def threadmanager(self):
        """
        Gets the threadmanager from the client if set
        """
        if hasattr(self.client, 'threadmanager'):
            return self.client.threadmanager
        return None

    @threadmanager.setter
    def threadmanager(self, threadmanager):
        """
        If the client is capable of receiving a threadmanager, set it

        @param threadmanager ThreadManager
        """
        Logger().info('Assigning ThreadManager to ProjectManager client')
        if hasattr(self.client, 'threadmanager'):
            self.client.threadmanager = threadmanager

    @property
    def server(self):
        """
        Get the server address of this client

        Clients providing this functionality must at the very least provide
        both server_address and attachments as properties to the return value,
        where attachments is a callback function.
        """
        return self._client.server


    def projects(self):
        """
        Get a list of projects defined in the agile project manager
        """
        return self.client.projects()

    @accepts(search_query=str, max_results=(bool, int), fields=(None, list), group_by=(None, str))
    def search_issues(self, search_query='', max_results=0, fields=None, group_by=None):
        """
        Search for issues

        @param search_query string     What to search for. When using the default manager, accepts queries in JQL
        @max_results        bool | int If False will load all issues in batches of 50
        @fields             list       A list of fields to retrieve as part of the query results
        """
        return self.client.search_issues(
            search_query=search_query,
            max_results=max_results,
            fields=fields,
            group_by=group_by
        )
