import os
from unittest import TestCase
from mock import call
from mock import patch
from mock import PropertyMock
from ddt import ddt, data, unpack
from collections import namedtuple
from releaseessentials.log import Logger
from releaseessentials.configuration import Configuration
from releaseessentials.managers.report import ReportManager
from releaseessentials.managers.thread import ThreadManager
from releaseessentials.resources import *
from tests.mocks.dataproviders import DataProviders
from releaseessentials.filter import Filter
from releaseessentials.parts.attachments import Attachments
from releaseessentials.exceptions import InvalidFilenameError

@ddt
class TestAttachments(TestCase):

    _report_manager = None
    _thread_manager = None

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    def setUp(self, mock_config, mock_parser):
        self.tearDown()
        path = os.path.dirname(os.path.realpath(__file__ + '../../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_config.return_value = [self._path]
        mock_parser.return_value = []
        Logger().debug('Loading configuration')
        config = None

        with patch('argparse.ArgumentParser.add_argument'):
            config = Configuration(filename='valid_config.json')
        config.check = True
        self._report_manager = ReportManager()
        self._thread_manager = ThreadManager()

    def tearDown(self):
        if ThreadManager._instance is not None:
            ThreadManager._instance = None
        if Configuration._instance is not None:
            del Configuration._instance
            Configuration._instance = None
        Configuration.NAMESPACE = 'releaseessentials'

        if Replacements._instance is not None:
            del Replacements._instance
            Replacements._instance = None

    @data(
        ('zip', 1, '/tmp/28/Jul/2016/AnotherTestApplication.zip'),
        ('sql', 1, '/tmp/28/Jul/2016/TestApplication.sql'),
        ('zip,sql', 2, ['/tmp/28/Jul/2016/AnotherTestApplication.zip', '/tmp/28/Jul/2016/TestApplication.sql'])
    )
    @patch('builtins.open', create=True)
    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @unpack
    def test_setup_and_run(
        self,
        collation,
        result_count,
        result_filename,
        mock_config_list,
        mock_results,
        mock_jira_client,
        mock_open
    ):
        mock_jira_client.return_value = None
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'releaseessentials'
        report = ReportManager()
        mock_results.return_value = DataProviders._test_data_for_attachments()

        report.add_callback('attachments', getattr(DataProviders, 'test_callback'))
        self.assertIsInstance(Configuration().replacements, Replacements)

        Config = namedtuple('Config', 'query fields collate output_path')
        config = Config(
            query='project=test and attachments is not empty',
            fields=[
                'key',
                'attachments'
            ],
            collate=collation,
            output_path='/tmp/{FIX_VERSION}'
        )

        attachments = None
        with patch('os.makedirs') as mock_os:
            attachments = Attachments(self._thread_manager, config)
            mock_os.assert_called_with('/tmp/28/Jul/2016')

        self._thread_manager.append(attachments)

        with patch('pycurl.Curl') as mock_curl:
            with patch('pycurl.Curl.setopt') as mock_setopt:
                with patch('pycurl.Curl.perform') as mock_perform:
                    with patch('pycurl.Curl.close') as mock_close:
                        Curl = namedtuple('Curl', 'URL WRITEDATA setopt perform close')
                        mock_curl.return_value = Curl(URL=None, WRITEDATA=None, setopt=mock_setopt, perform=mock_perform, close=mock_close)
                        self._thread_manager.execute()

                        self.assertEquals(result_count, len(attachments._content))
                        self.assertEquals((2 * result_count), mock_setopt.call_count)
                        self.assertEquals((1 * result_count), mock_perform.call_count)
                        self.assertEquals((1 * result_count), mock_close.call_count)
                        self.assertEquals((1 * result_count), mock_open.call_count)
                        calls = []
                        if isinstance(result_filename, list):
                            for filename in result_filename:
                                calls.append(call(filename, 'wb'))
                        else:
                            calls.append(call(result_filename, 'wb'))
                        mock_open.assert_has_calls(calls, any_order=True)

        with patch('releaseessentials.managers.report.ReportManager.add_paragraph') as mock_paragraph:
            with patch('releaseessentials.managers.report.ReportManager.add_list') as mock_list:
                attachments.render(report)
                mock_paragraph.assert_called_with('The following file(s) have been attached to this document:')
                mock_list.assert_called_with('TestFile.zip')

    @data(
        ('zip', 1, '/tmp/28/Jul/2016/AnotherTestApplication.zip'),
        ('sql', 1, '/tmp/28/Jul/2016/TestApplication.sql'),
        ('zip,sql', 2, ['/tmp/28/Jul/2016/AnotherTestApplication.zip', '/tmp/28/Jul/2016/TestApplication.sql'])
    )
    @patch('builtins.open', create=True)
    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @unpack
    def test_setup_and_run_without_callback(
        self,
        collation,
        result_count,
        result_filename,
        mock_config_list,
        mock_results,
        mock_jira_client,
        mock_open
    ):
        mock_jira_client.return_value = None
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'releaseessentials'
        report = ReportManager()
        report.add_callback('attachments', None)
        mock_results.return_value = DataProviders._test_data_for_attachments()

        self.assertIsInstance(Configuration().replacements, Replacements)

        Config = namedtuple('Config', 'query fields collate output_path')
        config = Config(
            query='project=test and attachments is not empty',
            fields=[
                'key',
                'attachments'
            ],
            collate=collation,
            output_path='/tmp/{FIX_VERSION}'
        )

        attachments = None
        with patch('os.makedirs') as mock_os:
            attachments = Attachments(self._thread_manager, config)
            mock_os.assert_called_with('/tmp/28/Jul/2016')

        self._thread_manager.append(attachments)

        with patch('pycurl.Curl') as mock_curl:
            with patch('pycurl.Curl.setopt') as mock_setopt:
                with patch('pycurl.Curl.perform') as mock_perform:
                    with patch('pycurl.Curl.close') as mock_close:
                        Curl = namedtuple('Curl', 'URL WRITEDATA setopt perform close')
                        mock_curl.return_value = Curl(URL=None, WRITEDATA=None, setopt=mock_setopt, perform=mock_perform, close=mock_close)
                        self._thread_manager.execute()

                        self.assertEquals(result_count, len(attachments._content))
                        self.assertEquals((2 * result_count), mock_setopt.call_count)
                        self.assertEquals((1 * result_count), mock_perform.call_count)
                        self.assertEquals((1 * result_count), mock_close.call_count)
                        self.assertEquals((1 * result_count), mock_open.call_count)
                        calls = []
                        if isinstance(result_filename, list):
                            for filename in result_filename:
                                calls.append(call(filename, 'wb'))
                        else:
                            calls.append(call(result_filename, 'wb'))
                        mock_open.assert_has_calls(calls, any_order=True)

        with patch('releaseessentials.managers.report.ReportManager.add_paragraph') as mock_paragraph:
            with patch('releaseessentials.managers.report.ReportManager.add_list') as mock_list:
                attachments.render(report)
                mock_paragraph.assert_not_called()
                mock_list.assert_not_called()

    @data(
        ('zip', 1, '/tmp/28/Jul/2016/AnotherTestApplication.zip'),
        ('sql', 1, '/tmp/28/Jul/2016/TestApplication.sql'),
        ('zip,sql', 2, ['/tmp/28/Jul/2016/AnotherTestApplication.zip', '/tmp/28/Jul/2016/TestApplication.sql'])
    )
    @patch('builtins.open', create=True)
    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @unpack
    def test_setup_and_run_where_callback_returns_string(
        self,
        collation,
        result_count,
        result_filename,
        mock_config_list,
        mock_results,
        mock_jira_client,
        mock_open
    ):
        mock_jira_client.return_value = None
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'releaseessentials'
        report = ReportManager()
        mock_results.return_value = DataProviders._test_data_for_attachments()

        report.add_callback('attachments', lambda x,y: 'TestFile.zip')
        self.assertIsInstance(Configuration().replacements, Replacements)

        Config = namedtuple('Config', 'query fields collate output_path')
        config = Config(
            query='project=test and attachments is not empty',
            fields=[
                'key',
                'attachments'
            ],
            collate=collation,
            output_path='/tmp/{FIX_VERSION}'
        )

        attachments = None
        with patch('os.makedirs') as mock_os:
            attachments = Attachments(self._thread_manager, config)
            mock_os.assert_called_with('/tmp/28/Jul/2016')

        self._thread_manager.append(attachments)

        with patch('pycurl.Curl') as mock_curl:
            with patch('pycurl.Curl.setopt') as mock_setopt:
                with patch('pycurl.Curl.perform') as mock_perform:
                    with patch('pycurl.Curl.close') as mock_close:
                        Curl = namedtuple('Curl', 'URL WRITEDATA setopt perform close')
                        mock_curl.return_value = Curl(URL=None, WRITEDATA=None, setopt=mock_setopt, perform=mock_perform, close=mock_close)
                        self._thread_manager.execute()

                        self.assertEquals(result_count, len(attachments._content))
                        self.assertEquals((2 * result_count), mock_setopt.call_count)
                        self.assertEquals((1 * result_count), mock_perform.call_count)
                        self.assertEquals((1 * result_count), mock_close.call_count)
                        self.assertEquals((1 * result_count), mock_open.call_count)
                        calls = []
                        if isinstance(result_filename, list):
                            for filename in result_filename:
                                calls.append(call(filename, 'wb'))
                        else:
                            calls.append(call(result_filename, 'wb'))
                        mock_open.assert_has_calls(calls, any_order=True)

        with patch('releaseessentials.managers.report.ReportManager.add_paragraph') as mock_paragraph:
            with patch('releaseessentials.managers.report.ReportManager.add_list') as mock_list:
                attachments.render(report)
                mock_paragraph.assert_called_with('The following file(s) have been attached to this document:')
                mock_list.assert_called_with('TestFile.zip')

    @data(
        ('zip,sql', 2, [])
    )
    @patch('builtins.open', create=True)
    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @unpack
    def test_setup_and_run_doesnt_download_if_attachments_is_empty(
        self,
        collation,
        result_count,
        result_filename,
        mock_config_list,
        mock_results,
        mock_jira_client,
        mock_open
    ):
        mock_jira_client.return_value = None
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'releaseessentials'
        report = ReportManager()
        mock_results.return_value = []

        report.add_callback('attachments', lambda x,y: '')
        self.assertIsInstance(Configuration().replacements, Replacements)

        Config = namedtuple('Config', 'query fields collate output_path')
        config = Config(
            query='project=test and attachments is not empty',
            fields=[
                'key',
                'attachments'
            ],
            collate=collation,
            output_path='/tmp/{FIX_VERSION}'
        )

        attachments = None
        with patch('os.makedirs') as mock_os:
            attachments = Attachments(self._thread_manager, config)
            mock_os.assert_called_with('/tmp/28/Jul/2016')

        with patch('releaseessentials.parts.attachments.Attachments._download_attachments') as mock_download:
            self._thread_manager.execute()
            mock_download.assert_not_called()

    @patch('releaseessentials.filter.Filter.failure', new_callable=PropertyMock)
    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    def test_setup_and_run_handles_exception(self, mock_config_list, mock_parser, mock_failure):
        mock_parser.return_value = []
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'releaseessentials'
        report = ReportManager()
        # never actually thrown from the filter but useful for testing and coverage ;-)
        mock_failure.return_value = InvalidFilenameError('The specified file does not exist')

        report.add_callback('test', 'test_callback')
        self.assertEquals('test_callback', report.get_callback('test'))
        self.assertIsInstance(Configuration().replacements, Replacements)

        Config = namedtuple('Config', 'query fields collate output_path')
        config = Config(
            query='project=test and attachments is not empty',
            fields=[
                'key',
                'attachments'
            ],
            collate='zip',
            output_path='/tmp/{FIX_VERSION}'
        )

        attachments = None
        with patch('os.makedirs') as mock_os:
            attachments = Attachments(self._thread_manager, config)
            mock_os.assert_called_with('/tmp/28/Jul/2016')

        with patch('releaseessentials.filter.Filter.failed', return_value=True):
            attachments.run()
            self.assertEquals(str(attachments._content.failure), 'The specified file does not exist')
