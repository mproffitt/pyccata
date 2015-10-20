import os
from unittest import TestCase
from mock import patch
from weeklyreport.managers.report import ReportManager
from weeklyreport.parts.paragraph import Paragraph
from weeklyreport.log import Logger
from weeklyreport.configuration import Configuration
from weeklyreport.managers.report import ReportManager
from weeklyreport.managers.thread import ThreadManager
from collections import namedtuple

class TestParagraph(TestCase):

    _report_manager = None

    #@patch('weeklyreport.log.Logger.log')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def setUp(self, mock_config):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_config.return_value = [self._path]
        #mock_log.return_value = None
        #Logger._instance = mock_log
        Logger().debug('Loading configuration')
        Configuration(filename='config_sections.json')
        self._report_manager = ReportManager()
        self._thread_manager = ThreadManager()

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'weeklyreport'

    @patch('weeklyreport.managers.report.ReportManager.add_paragraph')
    def test_init_sets_text(self, mock_paragraph):
        Config = namedtuple('Config', 'text')
        config = Config(text='some text')
        paragraph = Paragraph(self._thread_manager, config)
        paragraph.run()
        paragraph.render(self._report_manager)
        self.assertEquals(paragraph._content, 'some text')
        self.assertTrue(paragraph._complete)
        mock_paragraph.assert_called_with('some text')

