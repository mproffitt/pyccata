import os
from unittest import TestCase
from mock import call
from mock import patch
from weeklyreport.parts.table import Table
from weeklyreport.log import Logger
from weeklyreport.configuration import Configuration
from weeklyreport.managers.report import ReportManager
from weeklyreport.managers.thread import ThreadManager
from weeklyreport.exceptions import ArgumentValidationError
from weeklyreport.exceptions import InvalidQueryError
from collections import namedtuple
from weeklyreport.resources import *
from tests.mocks.dataproviders import DataProviders
from weeklyreport.filter import Filter

class TestTable(TestCase):

    _report_manager = None
    _thread_manager = None

    @patch('argparse.ArgumentParser.parse_args')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def setUp(self, mock_config, mock_parser):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_config.return_value = [self._path]
        mock_parser.return_value = []
        Logger().debug('Loading configuration')
        Configuration(filename='config_sections.json')
        self._report_manager = ReportManager()
        self._thread_manager = ThreadManager()

    def tearDown(self):
        if ThreadManager._instance is not None:
            ThreadManager._instance = None
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'weeklyreport'

    @patch('weeklyreport.managers.report.ReportManager.add_table')
    def test_run_creates_table(self, mock_manager):
        Config = namedtuple('Config', 'rows columns style')

        rows = []
        for i in range(6):
            rows.append(
                ['Row ' + str((i+1)), 'Test description ' + str((i+1))]
            )

        columns = [
            'Name',
            'Description'
        ]
        config = Config(rows=rows, columns=columns, style='Light heading 1')
        table = Table(self._thread_manager, config)
        self. _thread_manager.execute()
        table.render(self._report_manager)

        calls = [call(headings=columns, data=rows, style='Light heading 1')]
        mock_manager.assert_has_calls(calls)
