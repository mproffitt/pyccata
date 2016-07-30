import os
from unittest import TestCase
from mock import call
from mock import patch
from mock import PropertyMock
from releaseessentials.parts.table import Table
from releaseessentials.log import Logger
from releaseessentials.configuration import Configuration
from releaseessentials.managers.report import ReportManager
from releaseessentials.managers.thread import ThreadManager
from releaseessentials.exceptions import ArgumentValidationError
from releaseessentials.exceptions import InvalidQueryError
from collections import namedtuple
from releaseessentials.resources import *
from tests.mocks.dataproviders import DataProviders
from releaseessentials.filter import Filter

class TestTable(TestCase):

    _report_manager = None
    _thread_manager = None

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
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
        Configuration.NAMESPACE = 'releaseessentials'

    @patch('releaseessentials.managers.report.ReportManager.add_table')
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
        self._thread_manager.execute()
        table.render(self._report_manager)

        calls = [call(headings=columns, data=rows, style='Light heading 1')]
        mock_manager.assert_has_calls(calls)

    @patch('releaseessentials.managers.report.ReportManager.add_table')
    def test_create_table_manages_exception_if_filter_cannot_be_created(self, mock_manager):
        Config = namedtuple('Config', 'rows columns style')

        Filter = namedtuple('SubFilter', 'search_for bob')
        rows = Filter(search_for='project=mssportal', bob='fish')

        columns = [
            'Name',
            'Description'
        ]
        config = Config(rows=rows, columns=columns, style='Light heading 1')
        table = Table(self._thread_manager, config)

    def test_run_completes_if_filter_fails(self):
        mock_filter = Filter('bob', max_results=5, fields=None)
        mock_filter._failure = InvalidQueryError('query is wrong')
        Config = namedtuple('Config', 'rows columns style')
        config = Config(rows=[['My search', mock_filter]], columns=['Test column', 'Test Results'], style=None)
        table = Table(self._thread_manager, config)
        table.run()
        self.assertTrue(table._complete)

    def test_run_completes_if_filter_delays_in_completing(self):
        mock_filter = Filter('bob', max_results=5, fields=None)
        Config = namedtuple('Config', 'rows columns style')
        config = Config(rows=[['My search', mock_filter]], columns=['Test column', 'Test Results'], style=None)
        with patch('releaseessentials.threading.Threadable.complete', new_callable=PropertyMock) as mock_thread:
            table = Table(self._thread_manager, config)
            mock_thread.side_effect = [False, False, True]
            table.run()
            self.assertTrue(table._complete)

    @patch('releaseessentials.managers.report.ReportManager.add_table')
    @patch('releaseessentials.managers.report.ReportManager.add_heading')
    def test_table_doesnt_render_with_empty_filter_results(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        Filter = namedtuple('Filter', 'query max_results')
        rows = Filter(query='project=mssportal', max_results=5)

        columns = [
            'Name',
            'Description'
        ]
        config = Config(rows=rows, columns=columns, style='Light heading 1')
        table = Table(self._thread_manager, config)

        document = ReportManager()
        table.render(document)
        mock_table.assert_not_called()
        mock_heading.assert_not_called()

    @patch('releaseessentials.managers.report.ReportManager.add_table')
    @patch('releaseessentials.managers.report.ReportManager.add_heading')
    def test_table_renders_filter_results(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        with patch('releaseessentials.filter.Filter.results', new_callable=PropertyMock) as mock_results:
            ResultsList = namedtuple('ResultsList', 'total results')
            Result = namedtuple('Result', 'key release_text business_representative')
            mock_results.return_value = ResultsList(total=1, results=[
                Result(key='testproj-123', release_text='I am test text', business_representative='Bob Smith')
            ])
            Filter = namedtuple('Filter', 'query max_results')
            rows = Filter(query='project=mssportal', max_results=5)

            columns = [
                'Name',
                'Description'
            ]
            config = Config(rows=rows, columns=columns, style='Light heading 1')
            table = Table(self._thread_manager, config)

            document = ReportManager()
            table.render(document)
            self.assertEquals(1, mock_table.call_count)
            mock_heading.assert_not_called()

    @patch('releaseessentials.managers.report.ReportManager.add_table')
    @patch('releaseessentials.managers.report.ReportManager.add_heading')
    def test_table_renders_filter_results(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        with patch('releaseessentials.filter.Filter.results', new_callable=PropertyMock) as mock_results:
            ResultsList = namedtuple('ResultsList', 'total results')
            Result = namedtuple('Result', 'key release_text business_representative')
            mock_results.return_value = ResultsList(total=1, results=[
                Result(key='testproj-123', release_text='I am test text', business_representative='Bob Smith')
            ])
            Filter = namedtuple('Filter', 'query max_results')
            rows = Filter(query='project=mssportal', max_results=5)

            columns = [
                'Name',
                'Description'
            ]
            config = Config(rows=rows, columns=columns, style='Light heading 1')
            table = Table(self._thread_manager, config)
            table.title = 'Test Title'

            document = ReportManager()
            table.render(document)
            self.assertEquals(1, mock_table.call_count)
            self.assertEquals(1, mock_heading.call_count)
            mock_heading.assert_called_with('Test Title', 3)
