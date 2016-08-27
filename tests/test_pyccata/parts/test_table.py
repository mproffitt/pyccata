import os
from unittest import TestCase
from mock import call
from mock import patch
from mock import PropertyMock
from pyccata.core.parts.table import Table
from pyccata.core.log import Logger
from pyccata.core.configuration import Configuration
from pyccata.core.managers.report import ReportManager
from pyccata.core.managers.thread import ThreadManager
from pyccata.core.exceptions import ArgumentValidationError
from pyccata.core.exceptions import InvalidQueryError
from collections import namedtuple
from pyccata.core.resources import *
from tests.mocks.dataproviders import DataProviders
from pyccata.core.filter import Filter

from pyccata.core.resources import MultiResultList
from pyccata.core.resources import ResultList
from pyccata.core.resources import Issue

class TestTable(TestCase):

    _report_manager = None
    _thread_manager = None

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
        if ThreadManager._instance is not None:
            ThreadManager._instance = None
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'pyccata.core'

    @patch('pyccata.core.managers.report.ReportManager.add_table')
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

    @patch('pyccata.core.managers.report.ReportManager.add_table')
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
        mock_filter = Filter('bob', max_results=5, fields=None, namespace='pyccata.core')
        mock_filter._failure = InvalidQueryError('query is wrong')
        Config = namedtuple('Config', 'rows columns style')
        config = Config(rows=[['My search', mock_filter]], columns=['Test column', 'Test Results'], style=None)
        table = Table(self._thread_manager, config)
        table.run()
        self.assertTrue(table._complete)

    def test_run_completes_if_filter_delays_in_completing(self):
        mock_filter = Filter('bob', max_results=5, fields=None, namespace='pyccata.core')
        Config = namedtuple('Config', 'rows columns style')
        config = Config(rows=[['My search', mock_filter]], columns=['Test column', 'Test Results'], style=None)
        with patch('pyccata.core.threading.Threadable.complete', new_callable=PropertyMock) as mock_thread:
            table = Table(self._thread_manager, config)
            mock_thread.side_effect = [False, False, True]
            table.run()
            self.assertTrue(table._complete)

    @patch('pyccata.core.managers.report.ReportManager.add_table')
    @patch('pyccata.core.managers.report.ReportManager.add_heading')
    def test_table_doesnt_render_with_empty_filter_results(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        Filter = namedtuple('Filter', 'query max_results namespace')
        rows = Filter(query='project=mssportal', max_results=5, namespace='pyccata.core')

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

    @patch('pyccata.core.managers.report.ReportManager.add_table')
    @patch('pyccata.core.managers.report.ReportManager.add_heading')
    def test_table_renders_filter_results(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        with patch('pyccata.core.filter.Filter.results', new_callable=PropertyMock) as mock_results:
            ResultsList = namedtuple('ResultsList', 'total results')
            Result = namedtuple('Result', 'key release_text business_representative')
            mock_results.return_value = ResultsList(total=1, results=[
                Result(key='testproj-123', release_text='I am test text', business_representative='Bob Smith')
            ])
            Filter = namedtuple('Filter', 'query max_results namespace')
            rows = Filter(query='project=mssportal', max_results=5, namespace='pyccata.core')

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

    @patch('pyccata.core.managers.report.ReportManager.add_table')
    @patch('pyccata.core.managers.report.ReportManager.add_heading')
    def test_table_renders_filter_results_from_cell_query(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        with patch('pyccata.core.filter.Filter.results', new_callable=PropertyMock) as mock_results:
            ResultsList = namedtuple('ResultsList', 'total results')
            Result = namedtuple('Result', 'key release_text business_representative')
            mock_results.return_value = ResultsList(total=1, results=[
                Result(key='testproj-123', release_text='I am test text', business_representative='Bob Smith')
            ])
            Filter = namedtuple('Filter', 'query max_results namespace')
            rows = Filter(query='project=mssportal', max_results=5, namespace='pyccata.core')

            columns = [
                'Name',
                'Description'
            ]
            config = Config(rows=[['Data', rows]], columns=columns, style='Light heading 1')
            table = Table(self._thread_manager, config)
            table.title = 'Test Title'

            document = ReportManager()
            table.render(document)
            self.assertEquals(1, mock_table.call_count)
            self.assertEquals(1, mock_heading.call_count)
            mock_heading.assert_called_with('Test Title', 3)

    @patch('pyccata.core.managers.report.ReportManager.add_table')
    @patch('pyccata.core.managers.report.ReportManager.add_heading')
    def test_table_renders_filter_results_from_cell_query_continues_if_filter_errors(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        with patch('pyccata.core.filter.Filter.results', new_callable=PropertyMock) as mock_results:
            ResultsList = namedtuple('ResultsList', 'total results')
            Result = namedtuple('Result', 'key release_text business_representative')
            mock_results.return_value = ResultsList(total=1, results=[
                Result(key='testproj-123', release_text='I am test text', business_representative='Bob Smith')
            ])
            Filter = namedtuple('Filter', 'max_results namespace')
            rows = Filter(max_results=5, namespace='pyccata.core')

            columns = [
                'Name',
                'Description'
            ]
            config = Config(rows=[['Data', rows]], columns=columns, style='Light heading 1')
            table = Table(self._thread_manager, config)
            table.title = 'Test Title'

            document = ReportManager()
            table.render(document)
            self.assertEquals(1, mock_table.call_count)
            self.assertEquals(1, mock_heading.call_count)
            mock_heading.assert_called_with('Test Title', 3)

    @patch('pyccata.core.managers.report.ReportManager.add_table')
    @patch('pyccata.core.managers.report.ReportManager.add_heading')
    def test_table_renders_filter_results_multi_results_with_combine(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        with patch('pyccata.core.filter.Filter.results', new_callable=PropertyMock) as mock_results:
            results_set_one = ResultList(name='test results')
            result_issue = Issue()
            result_issue.description = 'This is a test item'
            results_set_one.append(result_issue)

            results_set_two = ResultList(name='another set of tests')
            another_result_issue = Issue()
            another_result_issue.description = 'This is a test item'
            results_set_two.append(another_result_issue)


            multi_results = MultiResultList()
            multi_results.combine = True
            multi_results.append(results_set_one)
            multi_results.append(results_set_two)

            mock_results.return_value = multi_results
            Filter = namedtuple('Filter', 'query max_results namespace')
            rows = Filter(query='project=mssportal', max_results=5, namespace='pyccata.core')

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

    @patch('pyccata.core.managers.report.ReportManager.add_table')
    @patch('pyccata.core.managers.report.ReportManager.add_heading')
    def test_table_renders_filter_results_multi_results_without_combine(self, mock_heading, mock_table):
        self.tearDown()
        Config = namedtuple('Config', 'rows columns style')

        with patch('pyccata.core.filter.Filter.results', new_callable=PropertyMock) as mock_results:
            results_set_one = ResultList(name='test results')
            result_issue = Issue()
            result_issue.description = 'This is a test item'
            results_set_one.append(result_issue)

            results_set_two = ResultList(name='another set of tests')
            another_result_issue = Issue()
            another_result_issue.description = 'This is a test item'
            results_set_two.append(another_result_issue)

            multi_results = MultiResultList()
            multi_results.combine = False
            multi_results.append(results_set_one)
            multi_results.append(results_set_two)

            mock_results.return_value = multi_results
            Filter = namedtuple('Filter', 'query max_results namespace')
            rows = Filter(query='project=mssportal', max_results=5, namespace='pyccata.core')

            columns = [
                'Name',
                'Description'
            ]
            config = Config(rows=rows, columns=columns, style='Light heading 1')
            table = Table(self._thread_manager, config)

            document = ReportManager()
            table.render(document)
            self.assertEquals(2, mock_table.call_count)
            self.assertEquals(2, mock_heading.call_count)



