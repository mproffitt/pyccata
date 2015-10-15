""" Wrapper class onto python-jira """
from weeklyreport.decorators    import accepts
from weeklyreport.interface     import ManagerInterface
from weeklyreport.configuration import Configuration
from jira.client                import JIRA, JIRAError
from weeklyreport.log           import Logger
from weeklyreport.exceptions    import InvalidConnectionError, InvalidQueryError

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

    @accepts(search_query=str, max_results=(bool, int), fields=list)
    def search_issues(self, search_query='', max_results=0, fields=list):
        """
        Search for issues in JIRA

        @param search_query string     A JQL formatted query
        @param max_results  [int|bool] If false will load all issues in batches of 50
        @param fields       list       A list of fields to include in the results
        """
        try:
            return self.client.search_issues(search_query, maxResults=max_results, fields=','.join(fields))
        except JIRAError as exception:
            raise InvalidQueryError(str(exception))

    def projects(self):
        """ Get a list of all projects defined in Jira """
        return self.client.projects()

