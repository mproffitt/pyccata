""" Wrapper class onto python-jira """
import re
from weeklyreport.decorators import accepts
from weeklyreport.interface import ManagerInterface
from weeklyreport.configuration import Configuration
from jira.client import JIRA
from jira.exceptions import JIRAError
from weeklyreport.log import Logger
from weeklyreport.exceptions import InvalidConnectionError
from weeklyreport.exceptions import InvalidQueryError
from weeklyreport.resources import ResultList
from weeklyreport.resources import Issue

class Jira(object):
    """ Jira management and searching class """
    __implements__ = (ManagerInterface,)
    _client = None
    _configuration = None
    _options = {}

    def __init__(self):
        """ Initialise Jira """
        Logger().info('Initialising Jira interface')
        if self.configuration.jira.port != '':
            self._options['server'] = self.configuration.jira.server + ':' + self.configuration.jira.port
        else:
            self._options['server'] = self.configuration.jira.server

    @property
    def client(self):
        """
        Lazy load the python-jira.client.JIRA object

        @return JIRA
        """
        if self._client is None:
            Logger().info('Establishing JIRA Api connection...')
            try:
                self._client = JIRA(
                    options=self._options,
                    basic_auth=(
                        self.configuration.jira.username,
                        self.configuration.jira.password
                    )
                )
                Logger().info('Connection success')
            except JIRAError as exception:
                Logger().error(
                    'Recieved HTTP/{code} whilst establishing connection to {server}'.format(
                        code=exception.status_code,
                        server=self._options['server']
                    )
                )
                Logger().error('Message was: \'{message}\''.format(message=exception.text))
                raise InvalidConnectionError(
                    exception.status_code,
                    self._options['server'],
                    exception.text,
                    exception.headers
                )
        return self._client

    @property
    def configuration(self):
        """
        Lazy load the Configuration singleton instance

        @return Configuration
        """
        if self._configuration is None:
            self._configuration = Configuration()
        return self._configuration

    @accepts(search_query=str, max_results=(bool, int), fields=(None, list))
    def search_issues(self, search_query='', max_results=0, fields=None):
        """
        Search for issues in JIRA

        @param search_query string     A JQL formatted query
        @param max_results  [int|bool] If false will load all issues in batches of 50
        @param fields       list       A list of fields to include in the results

        @return ResultSet
        """
        try:
            if type(fields) is list:
                fields = ','.join(fields)
            max_results = max_results if max_results != 0 else False
            results = self.client.search_issues(search_query, maxResults=max_results, fields=fields)
            return Jira._convert_results(results)
        except JIRAError as exception:
            expression = '.*Error in the JQL Query.*'
            if exception.status_code == 400 and re.match(expression, exception.text):
                raise InvalidQueryError(str(exception))
            raise InvalidConnectionError(
                exception.status_code,
                self._options['server'],
                exception.text,
                exception.headers
            )

    def projects(self):
        """ Get a list of all projects defined in Jira """
        return self.client.projects()

    @staticmethod
    @accepts(list)
    def _convert_results(results):
        """
        Converts a ``jira.client.ResultList`` of ``jira.resources.Issues`` into a
        ``weeklyreport.resources.ResultList`` of ``weeklyreport.resources.Issues``
        """
        result_set = ResultList()
        result_set.total = results.total if hasattr(results, 'total') else len(results)
        for issue in results:
            item = Issue()
            item.key = issue.key
            item.summary = getattr(issue.fields, 'summary') if hasattr(issue.fields, 'summary') else None
            item.issuetype = getattr(issue.fields, 'issuetype') if hasattr(issue.fields, 'issuetype') else None
            item.created = getattr(issue.fields, 'created') if hasattr(issue.fields, 'created') else None
            item.updated = getattr(issue.fields, 'updated') if hasattr(issue.fields, 'updated') else None
            item.priority = getattr(issue.fields, 'priority') if hasattr(issue.fields, 'priority') else None
            item.description = getattr(issue.fields, 'description') if hasattr(issue.fields, 'description') else None
            item.status = getattr(issue.fields, 'status') if hasattr(issue.fields, 'status') else None
            item.project = getattr(issue.fields, 'project') if hasattr(issue.fields, 'project') else None
            item.fixVersions = getattr(issue.fields, 'fixVersions') if hasattr(issue.fields, 'fixVersions') else None
            item.resolution = getattr(
                issue.fields, 'resolution'
            ) if hasattr(issue.fields, 'resolution') else None
            item.resolutiondate = getattr(
                issue.fields, 'resolutiondate'
            ) if hasattr(issue.fields, 'resolutiondate') else None
            item.creator = getattr(issue.fields, 'creator') if hasattr(issue.fields, 'creator') else None
            item.assignee = getattr(issue.fields, 'assignee') if hasattr(issue.fields, 'assignee') else None
            result_set.append(item)
        return result_set
