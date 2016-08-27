import os
from unittest import TestCase
from mock import call
from mock import patch
from mock import PropertyMock
from ddt import ddt, data, unpack
from collections import namedtuple
from pyccata.core.log import Logger
from pyccata.core.configuration import Configuration
from pyccata.core.managers.report import ReportManager
from pyccata.core.managers.thread import ThreadManager
from pyccata.core.resources import *
from tests.mocks.dataproviders import DataProviders
from pyccata.core.filter import Filter
from pyccata.core.parts.attachments import Attachments
from pyccata.core.exceptions import InvalidFilenameError
from pyccata.core.exceptions import InvalidCallbackError

@ddt
class TestAttachments(TestCase):

    _report_manager = None
    _thread_manager = None

    @patch('pyccata.core.log.Logger.log')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def setUp(self, mock_config, mock_parser, mock_log):
        self.tearDown()
        mock_log.return_value = None
        Logger._instance = mock_log
        path = os.path.dirname(os.path.realpath(__file__ + '../../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_config.return_value = [self._path]
        mock_parser.return_value = []
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
        Configuration.NAMESPACE = 'pyccata.core'

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
    @patch('pyccata.core.configuration.Configuration._get_locations')
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
        Configuration.NAMESPACE = 'pyccata.core'
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
        Replacements().find('FIX_VERSION').value = '28/Jul/2016'

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

        with patch('pyccata.core.managers.report.ReportManager.add_paragraph') as mock_paragraph:
            with patch('pyccata.core.managers.report.ReportManager.add_list') as mock_list:
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
    @patch('pyccata.core.configuration.Configuration._get_locations')
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
        Configuration.NAMESPACE = 'pyccata.core'
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
        Replacements().find('FIX_VERSION').value = '28/Jul/2016'

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

        with patch('pyccata.core.managers.report.ReportManager.add_paragraph') as mock_paragraph:
            with patch('pyccata.core.managers.report.ReportManager.add_list') as mock_list:
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
    @patch('pyccata.core.configuration.Configuration._get_locations')
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
        Configuration.NAMESPACE = 'pyccata.core'
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
        Replacements().find('FIX_VERSION').value = '28/Jul/2016'

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

        with patch('pyccata.core.managers.report.ReportManager.add_paragraph') as mock_paragraph:
            with patch('pyccata.core.managers.report.ReportManager.add_list') as mock_list:
                attachments.render(report)
                mock_paragraph.assert_called_with('The following file(s) have been attached to this document:')
                mock_list.assert_called_with('TestFile.zip')

    @data(
        ('zip,sql', 2, [])
    )
    @patch('builtins.open', create=True)
    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('pyccata.core.configuration.Configuration._get_locations')
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
        Configuration.NAMESPACE = 'pyccata.core'
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
        Replacements().find('FIX_VERSION').value = '28/Jul/2016'

        attachments = None
        with patch('os.makedirs') as mock_os:
            attachments = Attachments(self._thread_manager, config)
            mock_os.assert_called_with('/tmp/28/Jul/2016')

        with patch('pyccata.core.parts.attachments.Attachments._download_attachments') as mock_download:
            self._thread_manager.execute()
            mock_download.assert_not_called()

    @patch('pyccata.core.filter.Filter.failure', new_callable=PropertyMock)
    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def test_setup_and_run_handles_exception(self, mock_config_list, mock_parser, mock_failure):
        mock_parser.return_value = []
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'pyccata.core'
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
        Replacements().find('FIX_VERSION').value = '28/Jul/2016'

        attachments = None
        with patch('os.makedirs') as mock_os:
            attachments = Attachments(self._thread_manager, config)
            mock_os.assert_called_with('/tmp/28/Jul/2016')

        with patch('pyccata.core.filter.Filter.failed', return_value=True):
            attachments.run()
            self.assertEquals(str(attachments._content.failure), 'The specified file does not exist')

    @patch('builtins.open', create=True)
    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('pyccata.core.managers.subjects.jira.Jira.server', new_callable=PropertyMock)
    @patch('pyccata.core.configuration.Configuration._get_locations')
    @unpack
    def test_run_raises_type_error_if_attachments_callback_function_is_not_set(
        self,
        mock_config_list,
        mock_results,
        mock_jira_results,
        mock_jira_client,
        mock_open
    ):
        mock_jira_client.return_value = None
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'pyccata.core'
        report = ReportManager()
        report.add_callback('attachments', None)
        mock_jira_results.return_value = DataProviders._test_data_for_attachments()
        server = namedtuple('Server', 'server_address attachments')
        mock_results.return_value = server(server_address=None, attachments=None)

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
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('os.makedirs') as mock_os:
                attachments = Attachments(self._thread_manager, config)
                mock_os.assert_called_with('/tmp/' + Configuration().replacements.replace('{FIX_VERSION}'))

        self._thread_manager.append(attachments)

        with patch('pycurl.Curl') as mock_curl:
            with patch('pycurl.Curl.setopt') as mock_setopt:
                with patch('pycurl.Curl.perform') as mock_perform:
                    with patch('pycurl.Curl.close') as mock_close:
                        Curl = namedtuple('Curl', 'URL WRITEDATA setopt perform close')
                        mock_curl.return_value = Curl(URL=None, WRITEDATA=None, setopt=mock_setopt, perform=mock_perform, close=mock_close)
                        with self.assertRaises(InvalidCallbackError):
                            self._thread_manager.execute()
                        self.assertIsInstance(attachments.failure, InvalidCallbackError)
                        mock_setopt.assert_not_called()
                        mock_perform.assert_not_called()
                        mock_close.assert_not_called()
                        mock_open.assert_not_called()
