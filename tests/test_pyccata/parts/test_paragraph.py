import os
from unittest import TestCase
from mock import patch
from pyccata.core.managers.report import ReportManager
from pyccata.core.parts.paragraph import Paragraph
from pyccata.core.log import Logger
from pyccata.core.configuration import Configuration
from pyccata.core.managers.report import ReportManager
from pyccata.core.managers.thread import ThreadManager
from collections import namedtuple
from mock import call

class TestParagraph(TestCase):

    _report_manager = None

    @patch('pyccata.core.log.Logger.log')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def setUp(self, mock_config, mock_parser, mock_log):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_config.return_value = [self._path]
        mock_parser.return_value = []
        mock_log.return_value = None
        Logger._instance = mock_log
        Configuration(filename='config_sections.json')
        self._report_manager = ReportManager()
        self._thread_manager = ThreadManager()

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'pyccata.core'

    @patch('pyccata.core.managers.report.ReportManager.add_paragraph')
    def test_init_sets_text(self, mock_paragraph):
        Config = namedtuple('Config', 'text')
        config = Config(text='some text')
        paragraph = Paragraph(self._thread_manager, config)
        paragraph.run()
        paragraph.render(self._report_manager)
        self.assertEquals(paragraph._content, 'some text')
        self.assertTrue(paragraph._complete)
        mock_paragraph.assert_called_with('some text')

    @patch('pyccata.core.managers.report.ReportManager.add_run')
    @patch('pyccata.core.managers.report.ReportManager.add_paragraph')
    def test_execute_with_runs(self, mock_paragraph, mock_run):
        Run = namedtuple('Run', 'text style')
        content = [
            'This is a line of text',
            Run(text='This is bold text', style='bold'),
            'followed by another line'
        ]

        Config = namedtuple('Config', 'text')
        config = Config(text=content)
        paragraph = Paragraph(self._thread_manager, config)
        paragraph.run()
        paragraph.render(self._report_manager)
        self.assertTrue(paragraph._complete)
        mock_paragraph.assert_called_with('This is a line of text')
        calls = [
            call('This is bold text', style='bold'),
            call('followed by another line')
        ]
        mock_run.assert_has_calls(calls)


