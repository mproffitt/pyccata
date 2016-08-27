import os
from unittest import TestCase
from mock import call
from mock import patch
from mock import PropertyMock
from collections import namedtuple
from pyccata.core.parts.list import List
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

class TestList(TestCase):

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

    def test_get_item_raises_error_if_content_is_filter_and_filter_results_is_empty(self):
        list_contents = Filter('project=mssportal', max_results=5, fields=['id', 'description' ,'priority'])
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')
        unordered = List(self._thread_manager, config)
        with self.assertRaises(IndexError):
            item = unordered[0]

    def test_get_item_raises_error_if_content_is_list_and_results_is_none(self):
        list_contents = []
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')
        unordered = List(self._thread_manager, config)
        with self.assertRaises(IndexError):
            item = unordered[0]

    def test_set_item_raises_error_if_content_is_filter_and_filter_results_is_none(self):
        list_contents = Filter('project=mssportal', max_results=5, fields=['id', 'description' ,'priority'])
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')
        unordered = List(self._thread_manager, config)
        with self.assertRaises(IndexError):
            unordered[0] = 'hello world'

    def test_set_item_raises_error_if_content_is_list_and_results_is_none(self):
        list_contents = []
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')
        unordered = List(self._thread_manager, config)
        with self.assertRaises(IndexError):
            unordered[0] = 'hello world'

    def test_get_len_returns_length_of_self_if_content_is_list(self):
        list_contents = [
            'test 1',
            'test 2',
            'test 3'
        ]

        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')
        unordered = List(self._thread_manager, config)
        self.assertEqual(3, len(unordered))

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    def test_get_len_returns_length_of_filter_results_if_content_is_filter(self, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_single_query_in_config()

        list_contents = Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority'])

        mock_manager.return_value = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()
        self.assertEquals(5, len(unordered))


    def test_delete_item_if_content_is_list(self):
        list_contents = [
            'test 1',
            'test 2',
            'test 3'
        ]

        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')
        unordered = List(self._thread_manager, config)

        del unordered[2]
        self.assertEquals(2, len(unordered))

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    def test_delete_item_if_content_is_filter(self, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_single_query_in_config()

        list_contents = Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority'])
        mock_manager.return_value = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()

        del unordered[1]
        self.assertEquals(4, len(unordered))


    def test_reverse_list_if_content_is_list(self):
        list_contents = [
            'test 1',
            'test 2',
            'test 3'
        ]

        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')
        unordered = List(self._thread_manager, config)

        unordered = list(reversed(unordered))
        self.assertEquals('test 3', unordered[0])
        self.assertEquals('test 2', unordered[1])
        self.assertEquals('test 1', unordered[2])

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    def test_reverse_list_if_content_is_filter(self, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_single_query_in_config()

        list_contents = Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority'])
        mock_manager.return_value = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()

        unordered = list(reversed(unordered))
        self.assertEquals('This is test item 5', unordered[0].description)
        self.assertEquals('This is test item 4', unordered[1].description)
        self.assertEquals('This is test item 3', unordered[2].description)
        self.assertEquals('This is test item 2', unordered[3].description)
        self.assertEquals('This is test item 1', unordered[4].description)

    def test_list_contains_item_if_content_is_list(self):
        list_contents = [
            'test 1',
            'test 2',
            'test 3'
        ]

        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')
        unordered = List(self._thread_manager, config)

        self.assertTrue(('test 1' in unordered))

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    def test_list_contains_item_if_content_is_filter(self, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_single_query_in_config()

        list_contents = Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority'])
        mock_manager.return_value = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()

        self.assertTrue((result_list[3] in unordered))

    def test_setup_raises_argument_validation_error_if_style_is_invalid(self):
        Config = namedtuple('Config', 'content style field')
        config = Config(content=[], style='IAmInvalid', field='')
        with self.assertRaises(ArgumentValidationError):
            unordered = List(self._thread_manager, config)

    @patch('pyccata.core.managers.report.ReportManager.add_list')
    def test_init_creates_list(self, mock_list):
        list_contents = [
            'test item 1',
            'test item 2',
            'test item 3'
        ]
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='')

        calls = [call(item, style='ListBullet') for item in list_contents]
        unordered = List(self._thread_manager, config)
        unordered.run()
        unordered.render(self._report_manager)

        mock_list.assert_has_calls(calls)

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    @patch('pyccata.core.managers.report.ReportManager.add_list')
    def test_init_using_list_of_queries_creates_list(self, mock_list, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_list_of_queries_in_config()

        list_contents = [
            Filter('project=mssportal', max_results=5, fields=['id', 'description' ,'priority']),
            Filter('project=svcdesk', max_results=5, fields=['id', 'description' ,'priority']),
            Filter('project=mvs', max_results=5, fields=['id', 'description' ,'priority']),
        ]

        mock_manager.side_effect = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        calls = [call(item[0].description, style='ListBullet') for item in result_list]

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()

        unordered.render(self._report_manager)

        mock_list.assert_has_calls(calls)

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    @patch('pyccata.core.managers.report.ReportManager.add_list')
    def test_init_using_list_of_queries_and_strings_creates_list(self, mock_list, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_list_of_queries_and_strings_in_config()

        list_contents = [
            Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority']),
            "This is a string entry",
            Filter('project=svdesk', max_results=5, fields=['id', 'description' ,'priority']),
            Filter('project=mvp', max_results=5, fields=['id', 'description' ,'priority']),
            "This is another string entry"
        ]

        effect = [item for item in result_list if isinstance(item, ResultList)]

        mock_manager.side_effect = effect
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        calls = [call(item[0].description if isinstance(item, list) else item, style='ListBullet') for item in result_list]

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()

        unordered.render(self._report_manager)

        mock_list.assert_has_calls(calls)

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    @patch('pyccata.core.managers.report.ReportManager.add_list')
    def test_init_using_single_query_creates_list(self, mock_list, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_single_query_in_config()

        list_contents = Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority'])

        mock_manager.return_value = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        calls = [call(item.description, style='ListBullet') for item in result_list]

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()

        unordered.render(self._report_manager)

        mock_list.assert_has_calls(calls)

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    @patch('pyccata.core.managers.report.ReportManager.add_list')
    def test_init_using_list_of_queries_and_strings_continues_if_query_errors(self, mock_list, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_list_of_queries_and_strings_continues()

        list_contents = [
            Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority']),
            "This is a string entry",
            Filter('project=svdesk', max_results=5, fields=['id', 'description' ,'priority']),
            Filter('project=mvp', max_results=5, fields=['id', 'description' ,'priority']),
            "This is another string entry"
        ]

        effect = [item for item in result_list if isinstance(item, ResultList)]
        effect[1] = InvalidQueryError('The query you have provided is invalid')

        mock_manager.side_effect = effect
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        calls = [call(item[0].description if isinstance(item, list) else item, style='ListBullet') for item in result_list]
        del calls[2]

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()
        unordered.render(self._report_manager)
        mock_list.assert_has_calls(calls)

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    def test_list_contains_item_if_content_is_tuple(self, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_single_query_in_config()

        ListContents = namedtuple('ListContents', 'query fields')
        list_contents = ListContents('project=msportal', fields=['id', 'description' ,'priority'])
        mock_manager.return_value = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        unordered = List(self._thread_manager, config)
        self._thread_manager.execute()

        self.assertTrue((result_list[3] in unordered))

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    def test_list_fails_if_content_is_invalid_tuple(self, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_single_query_in_config()

        Filter = namedtuple('Filter', 'bob fields')
        list_contents = Filter('project=msportal', fields=['id', 'description' ,'priority'])
        mock_manager.return_value = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        with self.assertRaises(ArgumentValidationError):
            unordered = List(self._thread_manager, config)

    def test_run_completes_if_filter_delays_in_completing(self):
        ListContents = namedtuple('ListContents', 'query fields')
        list_contents = ListContents('project=msportal', fields=['id', 'description' ,'priority'])
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        with patch('pyccata.core.filter.Filter.complete', new_callable=PropertyMock) as mock_thread_complete:
            unordered = List(self._thread_manager, config)
            mock_thread_complete.side_effect = [False, False, True]
            unordered.run()
            self.assertTrue(unordered._complete)

    def test_run_completes_if_thread_fails(self):
        ListContents = namedtuple('ListContents', 'query fields')
        list_contents = ListContents('project=msportal', fields=['id', 'description' ,'priority'])
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        with patch('pyccata.core.threading.Threadable.complete', new_callable=PropertyMock) as mock_thread_complete:
            unordered = List(self._thread_manager, config)
            mock_thread_complete.return_value = True
            unordered._content._failure = InvalidQueryError('Your JQL contains an error before Pipeline')
            unordered.run()
            self.assertTrue(unordered._complete)

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    @patch('pyccata.core.managers.report.ReportManager.add_list')
    def test_init_using_list_of_queries_and_strings_continues_if_query_is_delayed(self, mock_list, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_list_of_queries_and_strings_continues()

        list_contents = [
            "This is a string entry",
            Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority'])
        ]

        effect = [item for item in result_list if isinstance(item, ResultList)]
        effect[1] = InvalidQueryError('The query you have provided is invalid')

        mock_manager.side_effect = effect
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        with patch('pyccata.core.filter.Filter.complete', new_callable=PropertyMock) as mock_thread_complete:
            mock_thread_complete.side_effect = [False, False, True]
            unordered = List(self._thread_manager, config)
            unordered.run()
            self.assertTrue(unordered._complete)

    @patch('pyccata.core.filter.Filter.results', new_callable=PropertyMock)
    @patch('pyccata.core.managers.report.ReportManager.add_list')
    def test_init_using_single_query_creates_list_of_items(self, mock_list, mock_results):

        results = [
            "test 1",
            "test 2",
            "test 3",
            "test 4",
            "test 5"
        ]

        resultset = Issue()
        resultset.pipelines = results

        list_contents = Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority'])
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='pipelines')

        calls = [call(item, style='ListBullet') for item in results]
        with patch('pyccata.core.filter.Filter.complete', new_callable=PropertyMock):
            unordered = List(self._thread_manager, config)
            mock_results.return_value = [resultset]
            list_contents.complete.return_value = True
            unordered.run()
            unordered.render(self._report_manager)
            mock_list.assert_has_calls(calls)

    @patch('pyccata.core.managers.project.ProjectManager.search_issues')
    def test_list_completes_if_content_filter_fails(self, mock_manager):
        result_list = DataProviders().get_results_for_list_init_with_single_query_in_config()

        list_contents = Filter('project=msportal', max_results=5, fields=['id', 'description' ,'priority'])
        mock_manager.return_value = result_list
        Config = namedtuple('Config', 'content style field')
        config = Config(content=list_contents, style='unordered', field='description')

        unordered = List(self._thread_manager, config)
        with patch('pyccata.core.filter.Filter.failure', new_callable=PropertyMock) as mock_failure:
            mock_failure.return_value = RuntimeError('I blew up')
            self._thread_manager.execute()


