import os
from unittest import TestCase
from mock import patch
from mock import call
from mock import PropertyMock
from collections import namedtuple
from releaseessentials.log import Logger
from releaseessentials.configuration import Configuration
from releaseessentials.managers.thread import ThreadManager
from releaseessentials.exceptions import ArgumentMismatchError
from releaseessentials.parts.section import Section
from releaseessentials.parts.paragraph import Paragraph
from releaseessentials.factory import DocumentPartFactory
from releaseessentials.managers.project import ProjectManager
from releaseessentials.managers.report import ReportManager
from releaseessentials.abstract import ThreadableDocument
from releaseessentials.document import DocumentController
from releaseessentials.filter import Filter

from tests.mocks.dataproviders import DataProviders
from tests.mocks.dataproviders import InvalidPriority

class TestSection(TestCase):

    _thread_manager = None

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.log.Logger.log')
    @patch('releaseessentials.configuration.Configuration._get_locations')
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
        Configuration.NAMESPACE = 'releaseessentials'

        if DocumentPartFactory._instance is not None:
            DocumentPartFactory._instance = None
        if ThreadManager._instance is not None:
            ThreadManager._instance = None

    def test_init_raises_argument_mismatch_error_if_keyword_args_differ(self):
        Config = namedtuple('Config', 'title, abstract config')
        config = Config(title='hello world', abstract='This is a test paragraph', config=['bob', 'marley', 'jimmy', 'hendrix'])

        with self.assertRaisesRegexp(ArgumentMismatchError, 'Invalid arguments provided to .*\. Got .* expected .*'):
            Section(self._thread_manager, config)

    @patch('releaseessentials.parts.section.Section._parse_structure')
    def test_threadable_init_calls_section_setup(self, mock_parse):
        mock_parse.return_value = []
        Config = namedtuple('Config', 'title, abstract level structure')
        config = Config(title='hello world', abstract='This is a test paragraph', level=0, structure=None)
        section = Section(self._thread_manager, config)
        self.assertEquals('hello world', section._title)
        self.assertEquals('This is a test paragraph', section._abstract._content[0])

    def test_parse_structure_returns_empty_list_if_structure_is_none(self):
        Config = namedtuple('Config', 'title, abstract level structure')
        config = Config(title='hello world', abstract='This is a test paragraph', level=0, structure=None)
        section = Section(self._thread_manager, config)
        self.assertIsInstance(section._structure, list)
        self.assertEquals(0, len(section._structure))

    def test_threadable_document_init_resets_priority_if_greater_than_max(self):
        Paragraph = namedtuple('Paragraph', 'text')
        Config = namedtuple('Config', 'title, abstract level structure')
        config = Config(title='hello world', abstract='This is a test paragraph', level=0, structure=None)
        section = Section(self._thread_manager, config)
        self.assertIsInstance(section._structure, list)
        self.assertEquals(0, len(section._structure))
        section._structure.append(InvalidPriority(self._thread_manager, Paragraph(text='hello world')))
        self.assertEquals(ThreadableDocument.MAX_DOCUMENT_PRIORITY, section._structure[len(section._structure)-1].PRIORITY)

    def test_parse_structure_returns_list_of_paragraphs(self):
        config = DataProviders.get_paragraph_config_for_section()
        section = Section(self._thread_manager, config)
        self.assertEquals(4, len(section._structure))
        for item in section._structure:
            self.assertIsInstance(item, Paragraph)

    def test_section_abstract_reads_abstract_from_file(self):
        Configuration._instance = DataProviders._get_config_for_test()
        Config = namedtuple('Config', 'title, abstract level structure')
        config = Config(title='hello world', abstract='section_test_text', level=0, structure=None)
        section = Section(self._thread_manager, config)
        self.assertEquals('hello world', section._title)
        self.assertEquals(3, len(section._abstract._content))

    @patch('releaseessentials.managers.report.ReportManager.add_paragraph')
    def test_section_render(self, mock_paragraph):
        Config = namedtuple('Config', 'title, abstract level structure')
        config = Config(title='hello world', abstract='section_test_text', level=0, structure=None)
        section = Section(self._thread_manager, config)
        section.render(ReportManager())

    @patch('releaseessentials.managers.report.ReportManager.add_paragraph')
    def test_render_calls_report_manager_add_methods(self, mock_paragraph):
        Configuration.report_text = 'tests/releaseessentials/data'
        config = DataProviders.get_paragraph_config_for_section()
        section = Section(self._thread_manager, config)
        self.assertEquals(4, len(section._structure))
        for item in section._structure:
            self.assertIsInstance(item, Paragraph)
        section.render(ReportManager())
        calls = [
            call('This is paragraph number 1'),
            call('This is paragraph number 3'),
            call('This is paragraph number 4'),
            call('This is paragraph number 5')
        ]
        mock_paragraph.assert_has_calls(calls)

    @patch('releaseessentials.managers.subjects.jira.Jira._client')
    @patch('releaseessentials.configuration.Configuration._load')
    def test_render_returns_if_section_contains_empty_table(self, mock_load, mock_jira_client):
        Rows = namedtuple('Row', 'query fields')

        row_config = Rows(query="project=bob and issuetype=Bug", fields=["key", "description", "priority"])
        #rows = Filter(row_config.query, fields=row_config.fields)
        #self._thread_manager.append(rows)
        columns = [
            'Name',
            'Description'
        ]

        TableConfig = namedtuple('TableConfig', 'rows columns style')
        table_config = TableConfig(rows=row_config, columns=columns, style='Light heading 1')

        StructureConfig = namedtuple('StructureConfig', 'type title content')
        structure_config = StructureConfig(type='table', title='Hello world', content=table_config)

        SectionConfig = namedtuple('SectionConfig', 'title abstract level structure')
        section_config = SectionConfig(
            title='Test',
            abstract='This is a test for empty tables',
            level=1,
            structure=[structure_config]
        )

        mock_jira_client.return_value = None
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('releaseessentials.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                section = Section(self._thread_manager, section_config)
                rows = section._structure[0].rows
                rows._thread_manager = self._thread_manager
                rows._project_manager = ProjectManager()
                rows.projectmanager._client._client = DataProviders._get_client_without_results()

                document = ReportManager()
                self._thread_manager.execute()
                section.render(document)

                self.assertEquals(0, rows.results.total)


