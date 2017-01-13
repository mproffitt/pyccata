import os
import glob
import shutil
from collections import namedtuple
from unittest import TestCase
from mock import patch
from mock import PropertyMock
from ddt import ddt, data, unpack

from pyccata.core.configuration import Configuration
from pyccata.core.managers.thread import ThreadManager
from pyccata.core.command import ThreadableCommand
from pyccata.core.managers.project import ProjectManager
from pyccata.core.log import Logger
from pyccata.core.exceptions import ThreadFailedError
from pyccata.core.pipeline import PipelineController
from pyccata.core.resources import Replacements

from tests.mocks.dataproviders import DataProviders

@ddt
class TestPipelineController(TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        self.tearDown()
        mock_log.return_value = None
        mock_parser.return_value = []
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        Logger._instance = mock_log

    def tearDown(self):
        Configuration.NAMESPACE = 'pyccata.core'
        if Configuration._instance is not None:
            Configuration._instance = None
        if Configuration._configuration is not None:
            Configuration._configuration = None

        if Replacements._instance is not None:
            del Replacements._instance
            Replacements._instance = None

    @patch('pyccata.core.configuration.Configuration._parse_flags')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def test_build_pipeline(self, mock_locations, mock_flags):
        mock_locations.return_value = [self._path]
        config = Configuration(filename='pipeline-config.json')
        config.check = True
        self._cleanup()

        pipeline = PipelineController()
        with patch('subprocess.Popen.poll') as mock_poll:
            with patch('subprocess.Popen._execute_child') as mock_command:
                with patch('subprocess.Popen.communicate') as mock_comms:
                    mock_comms.return_value = True
                    pipeline.build()
                    self.assertEquals(3, pipeline.length)

    def _cleanup(self):
        string = Replacements().replace('{BASE_PATH}') + '*'
        pattern = glob.glob(string)
        for path in pattern:
            shutil.rmtree(path)
        os.makedirs(Replacements().replace('{BASE_PATH}'))
