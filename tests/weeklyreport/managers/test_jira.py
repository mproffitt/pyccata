from unittest import TestCase
from mock     import patch, PropertyMock

from collections                import namedtuple
from weeklyreport.configuration import Configuration
from weeklyreport.manager       import ProjectManager
from weeklyreport.exceptions    import InvalidConnectionError, InvalidQueryError
from weeklyreport.interface     import ManagerInterface
from weeklyreport.managers.jira import Jira
from jira.client                import JIRA, JIRAError

class TestJira(TestCase):
    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_exception_on_client_initialisation_failure(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_jira_client.side_effect  = JIRAError(status_code = 500, text='something')
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test(port='')
                mock_manager.return_value = key
                with self.assertRaises(InvalidConnectionError) as cm:
                    manager = ProjectManager()
                    v = manager.client.client

                e = cm.exception
                self.assertEqual(500, e._code)
                self.assertEqual('something', e._error)
                self.assertRegexpMatches(str(e), 'Recieved HTTP\/\d+ whilst establishing connection to .*')


    @patch('weeklyreport.managers.jira.Jira._client')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_loads_client_on_success(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = TestJira._get_client()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager, ProjectManager)
                self.assertIsInstance(manager._client, Jira)
                self.assertTrue(issubclass(type(manager), ManagerInterface))
                self.assertTrue(issubclass(type(manager._client), ManagerInterface))

    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_returns_list_of_projects(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        data = TestJira._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                manager._client._client = TestJira._get_client()
                self.assertEqual(len(manager.projects()), 3)

    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_returns_search_result_list(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        data = TestJira._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                manager._client._client = TestJira._get_client()
                self.assertEqual(
                    manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[]),
                    TestJira._test_data_for_search_results()
                )

    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_exception_if_search_query_fails(self, mock_load, mock_search, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_search.side_effect = JIRAError(text = 'Query is invalid')

        data = TestJira._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                with self.assertRaisesRegexp(InvalidQueryError, 'Query is invalid'):
                    manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[])


    ###################################################################################################################
    # Data provider methods
    # =================================================================================================================
    @staticmethod
    def _get_client():
        JIRA = namedtuple('JIRA', 'search_issues projects')
        return JIRA(
            search_issues=lambda x, maxResults: TestJira._test_data_for_search_results(),
            projects=lambda: TestJira._test_data_for_projects()
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
    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_exception_on_client_initialisation_failure(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_jira_client.side_effect  = JIRAError(status_code = 500, text='something')
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test(port='')
                mock_manager.return_value = key
                with self.assertRaises(InvalidConnectionError) as cm:
                    manager = ProjectManager()
                    v = manager.client.client

                e = cm.exception
                self.assertEqual(500, e._code)
                self.assertEqual('something', e._error)
                self.assertRegexpMatches(str(e), 'Recieved HTTP\/\d+ whilst establishing connection to .*')


    @patch('weeklyreport.managers.jira.Jira._client')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_loads_client_on_success(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = TestJira._get_client()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager, ProjectManager)
                self.assertIsInstance(manager._client, Jira)
                self.assertTrue(issubclass(type(manager), ManagerInterface))
                self.assertTrue(issubclass(type(manager._client), ManagerInterface))

    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_returns_list_of_projects(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        data = TestJira._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                manager._client._client = TestJira._get_client()
                self.assertEqual(len(manager.projects()), 3)

    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_returns_search_result_list(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        data = TestJira._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                manager._client._client = TestJira._get_client()
                self.assertEqual(
                    manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[]),
                    TestJira._test_data_for_search_results()
                )

    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_exception_if_search_query_fails(self, mock_load, mock_search, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_search.side_effect = JIRAError(text = 'Query is invalid')

        data = TestJira._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = TestJira._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                with self.assertRaisesRegexp(InvalidQueryError, 'Query is invalid'):
                    manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[])


    ###################################################################################################################
    # Data provider methods
    # =================================================================================================================
    @staticmethod
    def _get_client():
        JIRA = namedtuple('JIRA', 'search_issues projects')
        return JIRA(
            search_issues=lambda x, maxResults: TestJira._test_data_for_search_results(),
            projects=lambda: TestJira._test_data_for_projects()
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
