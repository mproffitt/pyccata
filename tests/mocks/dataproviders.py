from time import sleep
from random import shuffle
from collections import namedtuple
from weeklyreport.threading import Threadable
from weeklyreport.interface import ObservableInterface
from weeklyreport.log import Logger
from weeklyreport.exceptions import InvalidQueryError
from weeklyreport.exceptions import InvalidConnectionError
from weeklyreport.filter import Filter

class TestObservableThread(Threadable):
    __implements__ = (ObservableInterface,)

    def setup(self):
        pass
    def run(self):
        pass

class ViableTestThread(Threadable):
    def setup(self):
        pass

    def run(self):
        Logger().info('Starting thread \'{0}\''.format(self._name))
        sleep(1)
        Logger().info('Thread \'{0}\' complete'.format(self._name))
        self._complete = True

class ExplodingQueryThread(Threadable):
    def setup(self):
        pass

    def run(self):
        Logger().info('Starting exploding thread \'{0}\''.format(self._name))
        self.failure = InvalidQueryError('Error in the JQL Query. Unknown field \'bob\'')

class BrokenConnectionThread(Threadable):
    def setup(self):
        pass

    @property
    def hasobservers(self):
        return False

    def run(self):
        Logger().info('Starting broken thread \'{0}\''.format(self._name))
        self.failure = InvalidConnectionError(500, 'http://jira.local:8080', 'Recieved HTTP/500 whilst establishing a connection to jira.local.')

class BrokenConnectionFilter(Filter):
    def run(self):
        Logger().info('Starting broken filter thread \'{0}\''.format(self._name))
        self.failure = InvalidConnectionError(500, 'http://jira.local:8080', 'Recieved HTTP/500 whilst establishing a connection to jira.local.')

class DataProviders(object):

    @staticmethod
    def some_threads_explode():
        threads = []
        for i in range(10):
            threads.append(ExplodingQueryThread())
            threads.append(BrokenConnectionThread())

        for i in range(80):
            threads.append(ViableTestThread())

        for i in range(5):
            shuffle(threads)
        return threads


    @staticmethod
    def _get_client():
        JIRA = namedtuple('JIRA', 'search_issues projects')
        return JIRA(
            search_issues=lambda x, maxResults, fields: DataProviders._test_data_for_search_results(),
            projects=lambda: DataProviders._test_data_for_projects()
        )

    @staticmethod
    def _test_data_for_projects():
        Project = namedtuple('Project', 'key name')
        return [
            Project(key='TP', name='Test Project'),
            Project(key='ATP', name='Another test project'),
            Project(key='BB', name='Bobs Board')
        ]

    @staticmethod
    def _test_data_for_search_results():
        Project = namedtuple('Project', 'key name')
        Assignee = namedtuple('Assignee', 'name displayName')
        Field = namedtuple('Field', 'assignee project')
        Issue = namedtuple('Issue', 'key fields')
        data = [
            Issue(
                key    = 'TP-123',
                fields = Field(
                    assignee=Assignee(
                        name='bob123',
                        displayName='Bob Smith'
                    ),
                    project=Project(
                        name='Test Project',
                        key='TP'
                    )
                )
            ),
            Issue(
                key    = 'ATP-114',
                fields = Field(
                    assignee=Assignee(
                        name='bob123',
                        displayName='Bob Smith'
                    ),
                    project=Project(
                        name='Another Test Project',
                        key='ATP'
                    )
                )
            )
        ]
        return data

    @staticmethod
    def _get_config_for_test(port='8080'):
        key = 'jira'
        Config = namedtuple('Config', 'manager jira server port username password')
        Jira   = Config(
            manager  = None,
            jira     = None,
            server   = 'http://jira.local',
            port     = port,
            username = 'test',
            password = 'letmein'
        )
        return Config(
            manager  = key,
            jira     = Jira,
            server   = None,
            port     = None,
            username = None,
            password = None
        )

