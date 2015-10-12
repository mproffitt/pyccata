from weeklyreport.decorators    import accepts
from weeklyreport.interface     import ManagerInterface
from weeklyreport.configuration import Configuration
from jira.client                import JIRA, JIRAError
from weeklyreport.log           import Logger
from weeklyreport.exceptions    import InvalidConnectionError, InvalidQueryError

class Jira(ManagerInterface):
    _client        = None
    _configuration = None
    _options       = {}

    def __init__(self):
        Logger().info('Initialising Jira interface')
        if self.configuration.jira.port != '':
            self._options['server'] = self.configuration.jira.server + ':' + self.configuration.jira.port
        else:
            self._options['server'] = self.configuration.jira.server

    @property
    def client(self):
        if self._client is None:
            Logger().info('Establishing JIRA Api connection...')
            try:
                self._client = JIRA(
                    options    = self._options,
                    basic_auth = (
                        self.configuration.jira.username,
                        self.configuration.jira.password
                    )
                )
                Logger().info('Connection success')
            except JIRAError as e:
                Logger().error(
                    'Recieved HTTP/{code} whilst establishing connection to {server}'.format(
                        code = e.status_code,
                        server = self._options['server']
                    )
                )
                Logger().error('Message was: \'{message}\''.format(message=e.text))
                raise InvalidConnectionError(e.status_code, self._options['server'], e.text, e.headers)
        return self._client

    @property
    def configuration(self):
        if self._configuration is None:
            self._configuration = Configuration()
        return self._configuration

    @accepts(search_query = str, max_results = (bool, int), fields = list)
    def search_issues(self, search_query = '', max_results = 0, fields = []):
        try:
            return self.client.search_issues(search_query, maxResults = max_results)
        except JIRAError as e:
            raise InvalidQueryError(str(e))

    def projects(self):
        return self.client.projects()

