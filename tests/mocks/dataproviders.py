import copy
from time import sleep
from random import shuffle
from collections import namedtuple
from weeklyreport.threading import Threadable
from weeklyreport.interface import ObservableInterface
from weeklyreport.log import Logger
from weeklyreport.exceptions import InvalidQueryError
from weeklyreport.exceptions import InvalidConnectionError
from weeklyreport.filter import Filter
from weeklyreport.manager import Manager
from weeklyreport.interface import ManagerInterface
from weeklyreport.interface import ReportingInterface
from weeklyreport.parts.paragraph import Paragraph
from weeklyreport.resources import *

class TestObservableThread(Threadable):
    __implements__ = (ObservableInterface,)
    PRIORITY = 9
    def setup(self):
        pass
    def run(self):
        pass

class ViableTestThread(Threadable):
    PRIORITY = 104
    def setup(self):
        pass

    def run(self):
        Logger().info('Starting thread \'{0}\''.format(self._name))
        sleep(1)
        Logger().info('Thread \'{0}\' complete'.format(self._name))
        self._complete = True

class ExplodingQueryThread(Threadable):
    PRIORITY = 2
    def setup(self):
        pass

    def run(self):
        Logger().info('Starting exploding thread \'{0}\''.format(self._name))
        self.failure = InvalidQueryError('Error in the JQL Query. Unknown field \'bob\'')

class BrokenConnectionThread(Threadable):
    PRIORITY = 4
    def setup(self):
        pass

    @property
    def hasobservers(self):
        return False

    def run(self):
        Logger().info('Starting broken thread \'{0}\''.format(self._name))
        self.failure = InvalidConnectionError(500, 'http://jira.local:8080', 'Recieved HTTP/500 whilst establishing a connection to jira.local.')

class BrokenConnectionFilter(Filter):
    PRIORITY = 1000
    def run(self):
        Logger().info('Starting broken filter thread \'{0}\''.format(self._name))
        self.failure = InvalidConnectionError(500, 'http://jira.local:8080', 'Recieved HTTP/500 whilst establishing a connection to jira.local.')

class InvalidRequires(Manager):
    def __init__(self):
        namespace = self.configuration.NAMESPACE
        self._load(namespace, self.configuration.manager, must_implement=ManagerInterface)

class InvalidReportRequires(Manager):
    def __init__(self):
        namespace = self.configuration.NAMESPACE
        self._load(namespace, self.configuration.reporting, must_implement=ReportingInterface)

class InvalidPriority(Paragraph):
    PRIORITY = 110
    def setup(self, text=''):
        self._content = text

    def run(self):
        self._complete = True


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
    def _get_config_for_test(port='8080', manager='jira', reporting='docx'):
        ReportType = namedtuple('Report', 'title subtitle abstract path datapath sections')
        Config = namedtuple('Config', 'manager reporting report jira server port username password')
        Report = ReportType(
            title='hello world',
            subtitle='sub title test',
            path='/path/to',
            datapath='tests/weeklyreport/data',
            sections=[None],
            abstract='An abstract block of text.\n\nSpanning two paragraphs...'
        )
        Jira   = Config(
            manager  = None,
            reporting= None,
            report   = None,
            jira     = None,
            server   = 'http://jira.local',
            port     = port,
            username = 'test',
            password = 'letmein'
        )

        return Config(
            manager  = manager,
            reporting= reporting,
            jira     = Jira,
            report   = Report,
            server   = None,
            port     = None,
            username = None,
            password = None
        )

    @staticmethod
    def _get_config_for_test_without_report(port='8080', manager='jira', reporting='docx'):
        Config = namedtuple('Config', 'manager reporting jira server port username password')
        Jira   = Config(
            manager  = None,
            reporting= None,
            jira     = None,
            server   = 'http://jira.local',
            port     = port,
            username = 'test',
            password = 'letmein'
        )

        return Config(
            manager  = manager,
            reporting= reporting,
            jira     = Jira,
            server   = None,
            port     = None,
            username = None,
            password = None
        )

    @staticmethod
    def _get_config_for_test_with_invalid_classes():
        ReportType = namedtuple('Report', 'title subtitle abstract path datapath sections')
        Config = namedtuple('Config', 'manager reporting report iwillneverbeamanager server port username password')
        Report = ReportType(
            title='hello world',
            subtitle='sub title test',
            path='/path/to',
            datapath='weeklyreport/data',
            sections=[None],
            abstract='An abstract block of text.\n\nSpanning two paragraphs...'
        )
        Jira   = Config(
            manager  = None,
            reporting= None,
            report   = None,
            iwillneverbeamanager  = None,
            server   = 'http://jira.local',
            port     = '8080',
            username = 'test',
            password = 'letmein'
        )

        return Config(
            manager  = 'iwillneverbeamanager',
            reporting= 'idonotexist',
            iwillneverbeamanager = Jira,
            report   = Report,
            server   = None,
            port     = None,
            username = None,
            password = None
        )

    @staticmethod
    def get_paragraph_config_for_section():
        InvalidText = namedtuple('InvalidText', 'content')
        Text = namedtuple('Text', 'text')
        Paragraph = namedtuple('Paragraph', 'type content')
        Section = namedtuple('Section', 'title abstract level structure')
        return Section(
            title='Hello world',
            abstract='This is a test abstract paragraph',
            level=0,
            structure=[
                Paragraph(type='paragraph', content=Text(text='This is paragraph number 1')),
                Paragraph(type='paragraph', content=InvalidText(content='This is paragraph number 2')),
                Paragraph(type='paragraph', content=Text(text='This is paragraph number 3')),
                Paragraph(type='paragraph', content=Text(text='This is paragraph number 4')),
                Paragraph(type='paragraph', content=Text(text='This is paragraph number 5'))
            ]
        )

    @staticmethod
    def get_results_for_list_init_with_list_of_queries_in_config():
        result_list = []

        for i in range(3):
            results = ResultList()
            issue = Issue()
            issue.description = 'This is test item ' + str((i+1))
            results.append(issue)
            result_list.append(copy.deepcopy(results))
            results = None

        return result_list

    @staticmethod
    def get_results_for_list_init_with_list_of_queries_and_strings_in_config():
        result_list = []

        for i in range(3):
            results = ResultList()
            issue = Issue()
            issue.description = 'This is test item ' + str((i+1))
            results.append(issue)
            result_list.append(copy.deepcopy(results))
            results = None
            if i == 0:
                result_list.append("This is a string entry"),
            elif i == 2:
                result_list.append("This is another string entry"),

        return result_list

    @staticmethod
    def get_results_for_list_init_with_list_of_queries_and_strings_continues():
        result_list = []

        for i in range(3):
            results = ResultList()
            issue = Issue()
            issue.description = 'This is test item ' + str((i+1))
            results.append(issue)
            result_list.append(copy.deepcopy(results))
            results = None
            if i == 0:
                result_list.append("This is a string entry"),
            elif i == 2:
                result_list.append("This is another string entry"),

        return result_list


    @staticmethod
    def get_results_for_list_init_with_single_query_in_config():
        result_list = ResultList()
        for i in range(5):
            issue = Issue()
            issue.description = 'This is test item ' + str((i+1))
            result_list.append(issue)

        return result_list

