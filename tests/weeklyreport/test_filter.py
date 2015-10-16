from unittest import TestCase
from mock import patch
from mock import PropertyMock

from weeklyreport.filter import Filter
from weeklyreport.managers.query import QueryManager
from weeklyreport.exceptions import InvalidQueryError
from weeklyreport.managers.project import ProjectManager
from tests.mocks.dataproviders import DataProviders

class TestFilter(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_run_raises_exception_if_manager_is_not_provided(self):
        mock_filter = Filter('issuetype = "Bug"')
        mock_filter.start()
        self.assertTrue(mock_filter.failed)
        self.assertIsInstance(mock_filter.failure, AssertionError)

    @patch('weeklyreport.managers.subjects.jira.Jira._client')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_run_raises_exception_if_query_fails(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = DataProviders._get_client()
        mock_jira_client.search_issues.side_effect = InvalidQueryError('The specified query is invalid')
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('iamnotavalidquery')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.start()
                self.assertTrue(mock_filter.failed)
                self.assertIsInstance(mock_filter.failure, InvalidQueryError)

    @patch('weeklyreport.managers.subjects.jira.Jira._client')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_run_marks_thread_as_complete_on_success(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('assignee = "Bob"')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client()
                mock_filter.start()
                self.assertTrue(mock_filter.complete)
                self.assertEqual(len(mock_filter.results), len(DataProviders._test_data_for_search_results()))

    @patch('weeklyreport.managers.subjects.jira.Jira._client')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_run_notifies_observers(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('assignee = "Bob"')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client()

                another_filter = Filter('assignee = "Bob"')
                mock_filter.append(another_filter)

                mock_filter.start()
                self.assertTrue(mock_filter.complete)
                self.assertEqual(len(mock_filter.results), len(DataProviders._test_data_for_search_results()))
                self.assertEqual(mock_filter._results, another_filter._results)

class TestQueryManager(TestCase):
    def setUp(self):
        self._manager = QueryManager()

    def tearDown(self):
        self._manager = None

    def test_append_updates_existing_items_observers_when_queries_match(self):
        mock_filter = Filter('assignee = "Bob"')
        another_filter = Filter('assignee = "Bob"')

        self._manager.append(mock_filter)
        self._manager.append(another_filter)
        self.assertEquals(1, len(self._manager))
        self.assertEquals(1, len(self._manager[0]._observers))

    def test_append_updates_self_items_observers_when_queries_match(self):
        mock_filter = Filter('assignee = "Foo"')
        another_filter = Filter('assignee = "Bar"')

        self._manager.append(mock_filter)
        self._manager.append(another_filter)
        self.assertEquals(2, len(self._manager))

