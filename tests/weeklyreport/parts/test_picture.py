import os
from unittest import TestCase
from mock import patch
from ddt import ddt, data, unpack
from collections import namedtuple

from weeklyreport.log import Logger
from weeklyreport.configuration import Configuration
from weeklyreport.managers.thread import ThreadManager
from weeklyreport.managers.report import ReportManager
from weeklyreport.parts.picture import Picture
from weeklyreport.exceptions import ThreadFailedError

@ddt
class TestPicture(TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    @patch('weeklyreport.log.Logger.log')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def setUp(self, mock_config, mock_log, mock_parser):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_config.return_value = [self._path]
        mock_log.return_value = None
        mock_parser.return_value = []
        Logger._instance = mock_log
        Configuration('config_sections.json')
        self._thread_manager = ThreadManager()

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'weeklyreport'
        if ThreadManager._instance is not None:
            ThreadManager._instance = None

    def test_setup_raises_file_not_found_error_if_file_not_found(self):
        Config = namedtuple('Config', 'filename width')
        config = Config(filename='mock_picture.png', width=20)
        with self.assertRaises(FileNotFoundError):
            picture = Picture(self._thread_manager, config)


    def test_width_raises_attribute_error_if_width_too_large(self):
        Config = namedtuple('Config', 'filename width')
        config = Config(filename='department.png', width=120)
        with self.assertRaises(AttributeError):
            picture = Picture(self._thread_manager, config)

    @data(
        (100, 5.7),
        (50, 2.85),
        (25., 1.425),
        (75.457, 4.301049)
    )
    @unpack
    def test_width_returns_inches(self, width, expected):
        Config = namedtuple('Config', 'filename width')
        config = Config(filename='department.png', width=width)
        picture = Picture(self._thread_manager, config)
        self.assertEquals(expected, picture.width)

    def test_render_fails_if_thread_has_not_been_executed(self):
        Config = namedtuple('Config', 'filename width')
        config = Config(filename='department.png', width=20)
        picture = Picture(self._thread_manager, config)
        with self.assertRaises(ThreadFailedError):
            picture.render(ReportManager())


    @patch('docx.document.Document.add_picture')
    @data(
        (100, 5.7),
        (50, 2.85),
        (25., 1.425),
        (75.457, 4.301049)
    )
    @unpack
    def test_render_image(self, width, expected, mock_picture):
        Config = namedtuple('Config', 'filename width')
        config = Config(filename='department.png', width=width)
        picture = Picture(self._thread_manager, config)
        picture.run()
        picture.render(ReportManager())
        mock_picture.assert_called_with(
            os.path.join(Configuration().report.datapath, config.filename),
            width=expected
        )

