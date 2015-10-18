from unittest import TestCase
from mock     import patch, PropertyMock
from collections import namedtuple
from weeklyreport.configuration import Configuration
from weeklyreport.interface import ReportingInterface
from weeklyreport.interface import ManagerInterface
from weeklyreport.exceptions import InvalidModuleError
from weeklyreport.exceptions import InvalidClassError
from weeklyreport.exceptions import RequiredKeyError
from weeklyreport.managers.report import ReportManager
from tests.mocks.dataproviders import InvalidReportRequires

class TestReportManager(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'weeklyreport.managers'

    @patch('weeklyreport.configuration.Configuration._load')
    def test_report_raises_invalid_module_error_if_report_module_does_not_exist(self, mock_load):
        with patch('weeklyreport.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'iamanoneexistantreport'
            with self.assertRaisesRegexp(InvalidModuleError, 'iamanoneexistantreport.*{0}.*'.format(Configuration.NAMESPACE)):
                ReportManager()

    @patch('weeklyreport.configuration.Configuration._load')
    def test_report_raises_invalid_class_error_if_report_class_does_not_exist(self, mock_load):
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('weeklyreport.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'reportmodule'
            with self.assertRaisesRegexp(InvalidClassError, 'Reportmodule .* {0}.*'.format(Configuration.NAMESPACE)):
                ReportManager()

    @patch('weeklyreport.configuration.Configuration._load')
    def test_report_raises_import_error_if_report_class_does_not_implement_reporting_interface(self, mock_load):
        Config = namedtuple('Config', 'reporting report path title subtitle abstract sections')
        Report = Config(reporting=None, report=None, path='/path/to', title='Test report', subtitle='A Subtitle', abstract='', sections='')
        self.tearDown()
        Configuration.NAMESPACE = 'tests.mocks'
        mock_config = Config(reporting='pdf', report=Report, path=None, title=None, subtitle=None, abstract=None, sections=None)
        Configuration._configuration = mock_config
        with patch('weeklyreport.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'pdf'
            with self.assertRaises(ImportError):
                a = ReportManager()

    @patch('weeklyreport.configuration.Configuration._load')
    def test_report_raises_not_implemented_error_if_report_class_has_no_requires(self, mock_load):
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('weeklyreport.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'docx'
            with self.assertRaises(NotImplementedError):
                a = InvalidReportRequires()

    @patch('weeklyreport.configuration.Configuration._load')
    def test_report_raises_required_key_error_if_config_has_invalid_requires(self, mock_load):
        Config = namedtuple('Config', 'reporting report path title subtitle abstract sections')
        Report = Config(reporting=None, report=None, path='/path/to', title='Test report', subtitle='A Subtitle', abstract='', sections='')
        mock_config = Config(reporting='docx', report=Report, path=None, title=None, subtitle=None, abstract=None, sections=None)

        self.tearDown()
        Configuration.NAMESPACE = 'tests.mocks'
        Configuration._configuration = mock_config
        with patch('weeklyreport.configuration.Configuration.reporting', new_callable=PropertyMock) as mock_report:
            mock_report.return_value = 'docx'
            InvalidReportRequires.REQUIRED = ['bob']
            with self.assertRaises(RequiredKeyError):
                a = InvalidReportRequires()

