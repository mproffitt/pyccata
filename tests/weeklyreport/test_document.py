""" Test module for weeklyreport.document """
import os
from unittest import TestCase
from mock import patch
from mock import PropertyMock
from mock import call
from ddt import ddt, data, unpack
from weeklyreport.exceptions import InvalidClassError
from weeklyreport.exceptions import InvalidModuleError
from weeklyreport.exceptions import RequiredKeyError
from weeklyreport.exceptions import ThreadFailedError
from weeklyreport.log import Logger
from weeklyreport.configuration import Configuration
from weeklyreport.managers.thread import ThreadManager
from weeklyreport.managers.report import ReportManager
from weeklyreport.factory import DocumentPartFactory
from weeklyreport.document import DocumentController

@ddt
class TestDocumentController(TestCase):

    @patch('weeklyreport.log.Logger.log')
    def setUp(self, mock_log):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_log.return_value = None
        Logger._instance = mock_log

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        if DocumentPartFactory._instance is not None:
            DocumentPartFactory._instance = None
        Configuration.NAMESPACE = 'weeklyreport'

    @patch('weeklyreport.configuration.Configuration._load')
    @data(
        (InvalidClassError, ('test','Class \'NeverDefined\' does not exist')),
        (InvalidModuleError, ('test', 'Module \'foobar\' does not exist')),
        (RequiredKeyError, ('\'Bob\' is a required key',)),
        (AttributeError, ('Invalid attribute \'foo\'',)),
        (IOError, ('The configuration file \'config.json\' cannot be found',))
    )
    @unpack
    def test_configuration_raises_exception(self, exception, message, mock_config):
        mock_config.side_effect = exception(*message)
        with self.assertRaises(exception):
            DocumentController()

    @patch('weeklyreport.manager.Manager._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    @data(
        (ImportError, 'Failed to import module \'idonotexist\''),
        (AttributeError, 'Invalid attribute \'foo\''),
        (NotImplementedError, 'Method has not been implemented'),
        (RequiredKeyError, '\'Bob\' is a required key')
    )
    @unpack
    def test_thread_manager_raises_exception(self, exception, message, mock_config, mock_manager_load):
        mock_manager_load.side_effect = exception(message)
        mock_config.return_value = [self._path]
        Configuration('config_sections.json')
        with self.assertRaises(exception):
            DocumentController()

    @patch('weeklyreport.document.DocumentController.threadmanager')
    @patch('weeklyreport.manager.Manager._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    @data(
        (ImportError, 'Failed to import module \'idonotexist\''),
        (AttributeError, 'Invalid attribute \'foo\''),
        (NotImplementedError, 'Method has not been implemented'),
        (RequiredKeyError, '\'Bob\' is a required key')
    )
    @unpack
    def test_report_manager_raises_exception(self, exception, message, mock_config, mock_manager_load, mock_thread_manager):
        mock_thread_manager.return_value = None
        mock_manager_load.side_effect = exception(message)
        mock_config.return_value = [self._path]
        Configuration('config_sections.json')
        with self.assertRaises(exception):
            DocumentController()

    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_report_manager_raises_invalid_module_error_if_parts_module_doesnt_exist(self, mock_config):
        mock_config.return_value = [self._path]
        Configuration('config_sections.json')
        with self.assertRaises(InvalidModuleError):
            with patch('weeklyreport.factory.DocumentPartFactory.MODULE', new_callable=PropertyMock) as mock_module:
                mock_module.return_value = 'pts'
                DocumentController()

    @patch('weeklyreport.document.DocumentController.reportmanager')
    @patch('weeklyreport.document.DocumentController.threadmanager')
    @patch('weeklyreport.document.DocumentController.configuration')
    @patch('importlib.import_module')
    def test_report_manager_raises_invalid_module_error_if_importlib_fails(self, mock_import, mock_config, mock_thread, mock_report):
        mock_report.return_value = None
        mock_thread.return_value = None
        mock_config.return_value = None
        mock_import.side_effect = ImportError('Failed to load module')
        with self.assertRaises(InvalidModuleError):
            DocumentController()

    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_report_manager_loads_document_part_factory(self, mock_config):
        mock_config.return_value = [self._path]
        Configuration('config_sections.json')
        document = DocumentController()
        self.assertIsInstance(document.configuration, Configuration)
        self.assertIsInstance(document.threadmanager, ThreadManager)
        self.assertIsInstance(document.reportmanager, ReportManager)
        self.assertIsInstance(document.partfactory, DocumentPartFactory)

    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_build_raises_exception_if_parts_class_does_not_exist(self, mock_config):
        mock_config.return_value = [self._path]
        with self.assertRaises(InvalidClassError):
            Configuration('invalid_report_parts.json')
            document = DocumentController()
            document.build()

    @patch('weeklyreport.configuration.Configuration._get_locations')
    @patch('weeklyreport.managers.thread.ThreadManager.__init__')
    def test_threadmanager_raises_exception_during_initialisation(self, mock_threadmanager, mock_config):
        mock_config.return_value = [self._path]
        Configuration('config_sections.json')
        mock_threadmanager.side_effect = AttributeError('Invalid attribute \'foo\' for manager ThreadManager')
        with self.assertRaises(AttributeError):
            DocumentController()

    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_document_raises_thread_failed_error_if_threadmanager_execute_returns_false(self, mock_config):
        mock_config.return_value = [self._path]
        Configuration('config_simple.json')
        document = DocumentController()
        with patch('weeklyreport.managers.thread.ThreadManager.execute') as mock_thread:
            mock_thread.return_value = False
            with self.assertRaises(ThreadFailedError):
                document.build()



    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_thread_manager_builds_simple_configuration(self, mock_config):
        mock_config.return_value = [self._path]
        Configuration('config_simple.json')
        document = DocumentController()
        self.assertIsInstance(document.configuration, Configuration)
        self.assertIsInstance(document.threadmanager, ThreadManager)
        self.assertIsInstance(document.reportmanager, ReportManager)
        self.assertIsInstance(document.partfactory, DocumentPartFactory)
        with patch('docx.document.Document.add_heading') as mock_heading, \
            patch('docx.document.Document.add_paragraph') as mock_paragraph, \
            patch('docx.document.Document.save') as mock_save:
                document.build()
                document.save('demo.docx')

        heading_calls = [
            call('Test document structure for WeeklyReport/Helicopter view', 0),
            call('Week 41', 1),
            call('hello world', 1),
            call('This has sub-sections', 1),
            call('this is sub section 1', 2),
            call('this is sub section 2', 2),
            call('This section uses a file path for its text', 1)
        ]
        self.assertEquals(mock_heading.call_count, len(heading_calls))
        mock_heading.assert_has_calls(heading_calls)
        self.assertEquals(17, mock_paragraph.call_count)
        mock_save.assert_called_with('demo.docx')

