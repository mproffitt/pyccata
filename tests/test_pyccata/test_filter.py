from unittest import TestCase
from mock import patch
from mock import PropertyMock
from ddt import ddt, data, unpack

from datetime import datetime
from collections import namedtuple
from pyccata.core.filter import Filter
from pyccata.core.managers.query import QueryManager
from pyccata.core.exceptions import InvalidQueryError
from pyccata.core.exceptions import InvalidModuleError
from pyccata.core.managers.project import ProjectManager
from tests.mocks.dataproviders import DataProviders
from pyccata.core.log import Logger
from pyccata.core.collation import _today
from pyccata.core.resources import ResultList
from pyccata.core.resources import MultiResultList
from pyccata.core.resources import Issue

@ddt
class TestFilter(TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        mock_log.return_value = None
        mock_parser.return_value = None
        Logger._instance = mock_log

    def tearDown(self):
        pass

    def test_run_raises_exception_if_manager_is_not_provided(self):
        mock_filter = Filter('issuetype = "Bug"', namespace='pyccata.core')
        mock_filter.start()
        self.assertTrue(mock_filter.failed)
        self.assertIsInstance(mock_filter.failure, AssertionError)

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_run_raises_exception_if_query_fails(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = DataProviders._get_client()
        mock_jira_client.search_issues.side_effect = InvalidQueryError('The specified query is invalid')
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('iamnotavalidquery', namespace='pyccata.core')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.start()
                self.assertTrue(mock_filter.failed)
                self.assertIsInstance(mock_filter.failure, InvalidQueryError)

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_run_marks_thread_as_complete_on_success(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('assignee = "Bob"', namespace='pyccata.core')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client()
                mock_filter.run()
                self.assertTrue(mock_filter.complete)
                self.assertEqual(len(mock_filter.results), len(DataProviders._test_data_for_search_results()))

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_run_notifies_observers(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('assignee = "Bob"', namespace='pyccata.core')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client()

                another_filter = Filter('assignee = "Bob"', namespace='pyccata.core')
                mock_filter.append(another_filter)

                mock_filter.run()
                self.assertEquals(mock_filter.failure, None)
                self.assertTrue(mock_filter.complete)
                self.assertEqual(len(mock_filter.results), len(DataProviders._test_data_for_search_results()))
                self.assertEqual(mock_filter._results, another_filter._results)

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_run_observer_skips_observer_implementation_if_results_have_been_set(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('assignee = "Bob"', namespace='pyccata.core')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client()

                another_filter = Filter('assignee = "Bob"', namespace='pyccata.core')
                another_filter.projectmanager = mock_filter.projectmanager
                mock_filter.append(another_filter)

                mock_filter.run()
                self.assertTrue(mock_filter.complete)
                self.assertEqual(mock_filter._results, another_filter._results)
                another_filter.start()
                self.assertEqual(len(mock_filter.results), len(DataProviders._test_data_for_search_results()))

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_results_with_collation_method_that_doesnt_exist(self, mock_load, mock_jira_client):
        collation = 'iamamethodwhichwillneverexist'
        distinct = False
        mock_jira_client.return_value = None
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                with self.assertRaises(InvalidModuleError):
                    mock_filter = Filter(
                        'assignee = "Bob"',
                        collate=collation,
                        distinct=distinct,
                        namespace='pyccata.core'
                    )
                #mock_filter.projectmanager = ProjectManager()
                #mock_filter.projectmanager._client._client = DataProviders._get_client_for_collation()
                #mock_filter.run()
                #self.assertTrue(mock_filter.complete)
                #self.assertEqual(7, len(mock_filter.results))

    @data(
        [namedtuple('Config', 'method field')(method='total_by_field', field='summary'), False, 3],
        [namedtuple('Config', 'method field')(method='total_by_field', field='summary'), True, 2],
        ['average_days_since_creation', False, '734 days'],
        ['average_days_since_creation', True, '734 days'],
        ['average_duration', False, '616 days'],
        ['average_duration', True, '616 days'],
        ['priority', False, namedtuple('Priority', 'critical high medium low lowest')(critical=1, high=1, medium=4, low=0, lowest=0)],
        ['priority', True, namedtuple('Priority', 'critical high medium low lowest')(critical=1, high=1, medium=4, low=0, lowest=0)],
        [namedtuple('Config', 'method field')(method='flatten', field='pipelines'), False, ['Foo', 'Bar', 'Bar']],
        [namedtuple('Config', 'method field')(method='flatten', field='pipelines'), True, ['Bar', 'Foo']]
    )
    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    @unpack
    def test_results_with_collation(self, collation, distinct, results, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter(
                    'assignee = "Bob"',
                    collate=collation,
                    distinct=distinct,
                    namespace='pyccata.core'
                )
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client_for_collation()
                mock_filter.run()
                self.assertTrue(mock_filter.complete)
                self.assertIsInstance(_today(), datetime)
                with patch(
                    'pyccata.core.collation._today', new_callable=(
                        lambda: datetime.strptime('2016-08-18', '%Y-%m-%d')
                    )
                ):
                    self.assertEqual(results, mock_filter.results)
