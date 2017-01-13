from unittest import TestCase
from mock     import patch, PropertyMock

from tests.mocks.dataproviders import DataProviders
from tests.mocks.dataproviders import TestObservableThread
from tests.mocks.dataproviders import ViableTestThread
from tests.mocks.dataproviders import BrokenConnectionFilter

from pyccata.core.configuration import Configuration
from pyccata.core.managers.project import ProjectManager
from pyccata.core.managers.thread import ThreadManager
from pyccata.core.managers.query import QueryManager
from pyccata.core.exceptions import InvalidModuleError
from pyccata.core.exceptions import ArgumentValidationError
from pyccata.core.exceptions import InvalidClassError
from pyccata.core.filter import Filter
from pyccata.core.log import Logger

class TestThreadManager(TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        mock_log.return_value = None
        mock_parser.return_value = []
        Logger._instance = mock_log

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        if ThreadManager._instance is not None:
            ThreadManager._instance = None

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_we_only_accept_threadable_objects(self, mock_load, mock_jira_client):
        with self.assertRaises(ArgumentValidationError):
            manager = ThreadManager()
            manager.append(object())


    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_adding_filter_adds_project_manager(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = DataProviders._get_client()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                manager = ThreadManager()
                self.assertIsInstance(manager.projectmanager, ProjectManager)
                self.assertIsInstance(manager.querymanager, QueryManager)
                self.assertIsInstance(manager.configuration, Configuration)
                mock_filter = Filter('assignee = "Foo"')
                manager.append(mock_filter)
                self.assertIsInstance(mock_filter.projectmanager, ProjectManager)

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    @patch('pyccata.core.managers.query.QueryManager.append')
    def test_adding_filter_ignores_argument_validation_error_and_adds_to_self(self, mock_query, mock_load, mock_jira_client):
        mock_query.side_effect = ArgumentValidationError('1st', 'append', 'pyccata.core.filter.Filter', 'object')
        mock_jira_client.return_value = DataProviders._get_client()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                manager = ThreadManager()
                manager.append(TestObservableThread())
                self.assertEquals(1, len(manager))

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    @patch('pyccata.core.managers.query.QueryManager.append')
    def test_execute_batches_pool_size_and_fills_on_complete(self, mock_query, mock_load, mock_jira_client):
        mock_query.side_effect = ArgumentValidationError('1st', 'append', 'pyccata.core.filter.Filter', 'object')
        mock_jira_client.return_value = DataProviders._get_client()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'

                manager = ThreadManager()
                # start with 100 threads...
                for i in range(100):
                    manager.append(ViableTestThread())
                manager.start()

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    @patch('pyccata.core.managers.query.QueryManager.append')
    def test_execute_batches_pool_size_and_logs_on_error(self, mock_query, mock_load, mock_jira_client):
        mock_query.side_effect = ArgumentValidationError('1st', 'append', 'pyccata.core.filter.Filter', 'object')
        mock_jira_client.return_value = DataProviders._get_client()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'

                manager = ThreadManager()
                test_threads = DataProviders.some_threads_explode()
                for thread in test_threads:
                    manager.append(thread)
                manager.start()

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_execute_retries_observers_on_error(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'

                mock_broken = BrokenConnectionFilter('assignee = "Bob"')
                mock_filter = Filter('assignee = "Bob"')

                manager = ThreadManager()
                manager.append(mock_broken)
                manager.append(mock_filter)
                mock_filter.projectmanager._client._client = DataProviders._get_client()

                self.assertEquals(1, len(manager))
                self.assertEquals(1, len(manager[0]._observers))
                manager.start()

    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_execute_adds_to_failures_when_all_observers_fail(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'

                mock_broken = BrokenConnectionFilter('assignee = "Bob"')
                mock_filter = BrokenConnectionFilter('assignee = "Bob"')

                manager = ThreadManager()
                manager.append(mock_broken)
                manager.append(mock_filter)

                self.assertEquals(1, len(manager))
                self.assertEquals(1, len(manager[0]._observers))
                manager.start()
                self.assertEquals(1, len(manager._failed_threads))

