import os
from unittest import TestCase
from mock     import patch, PropertyMock
from collections import namedtuple
from releaseessentials.configuration import Configuration
from releaseessentials.interface import ReportingInterface
from releaseessentials.interface import ManagerInterface
from releaseessentials.exceptions import InvalidModuleError
from releaseessentials.exceptions import InvalidClassError
from releaseessentials.exceptions import RequiredKeyError
from releaseessentials.managers.report import ReportManager
from tests.mocks.dataproviders import InvalidReportRequires
from releaseessentials.log import Logger

class TestReportManager(TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_log.return_value = None
        mock_parser.return_value = None
        self._mock_log = mock_log

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'releaseessentials'

    @patch('releaseessentials.configuration.Configuration._load')
    def test_report_raises_invalid_module_error_if_report_module_does_not_exist(self, mock_load):
        with patch('releaseessentials.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'iamanoneexistantreport'
            with self.assertRaisesRegexp(InvalidModuleError, 'iamanoneexistantreport.*{0}.*'.format(Configuration.NAMESPACE)):
                ReportManager()

    @patch('releaseessentials.configuration.Configuration._load')
    def test_report_raises_invalid_class_error_if_report_class_does_not_exist(self, mock_load):
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('releaseessentials.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'reportmodule'
            with self.assertRaisesRegexp(InvalidClassError, 'Reportmodule .* {0}.*'.format(Configuration.NAMESPACE)):
                ReportManager()

    @patch('releaseessentials.configuration.Configuration._load')
    def test_report_raises_import_error_if_report_class_does_not_implement_reporting_interface(self, mock_load):
        Config = namedtuple('Config', 'reporting report path title subtitle abstract sections')
        Report = Config(reporting=None, report=None, path='/path/to', title='Test report', subtitle='A Subtitle', abstract='', sections='')
        self.tearDown()
        Configuration.NAMESPACE = 'tests.mocks'
        mock_config = Config(reporting='pdf', report=Report, path=None, title=None, subtitle=None, abstract=None, sections=None)
        Configuration._configuration = mock_config
        with patch('releaseessentials.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'pdf'
            with self.assertRaises(ImportError):
                a = ReportManager()

    @patch('releaseessentials.configuration.Configuration._load')
    def test_report_raises_not_implemented_error_if_report_class_has_no_requires(self, mock_load):
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('releaseessentials.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'docx'
            with self.assertRaises(NotImplementedError):
                a = InvalidReportRequires()

    @patch('releaseessentials.configuration.Configuration._load')
    def test_report_raises_required_key_error_if_config_has_invalid_requires(self, mock_load):
        Config = namedtuple('Config', 'reporting report path title subtitle abstract sections')
        Report = Config(reporting=None, report=None, path='/path/to', title='Test report', subtitle='A Subtitle', abstract='', sections='')
        mock_config = Config(reporting='docx', report=Report, path=None, title=None, subtitle=None, abstract=None, sections=None)

        self.tearDown()
        Configuration.NAMESPACE = 'tests.mocks'
        Configuration._configuration = mock_config
        with patch('releaseessentials.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'docx'
            InvalidReportRequires.REQUIRED = ['bob']
            with self.assertRaises(RequiredKeyError):
                a = InvalidReportRequires()

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    def test_report_callback_returns_none_if_callback_has_not_been_added(self, mock_config_list, mock_parser):
        mock_parser.return_value = []
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'releaseessentials'
        config = Configuration(filename='valid_config.json')
        config.check = True
        report = ReportManager()
        report.add_callback('test', 'test_callback')
        self.assertEquals(None, report.get_callback('bob'))

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    def test_report_callback_returns_callback(self, mock_config_list, mock_parser):
        mock_parser.return_value = []
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'releaseessentials'
        config = Configuration(filename='valid_config.json')
        config.check = True
        report = ReportManager()
        report.add_callback('test', 'test_callback')
        self.assertEquals('test_callback', report.get_callback('test'))
