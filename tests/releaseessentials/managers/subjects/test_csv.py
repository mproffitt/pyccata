import os

from unittest import TestCase
from mock import patch, call, PropertyMock
import pandas
from collections import namedtuple
from releaseessentials.configuration import Configuration
from releaseessentials.managers.thread import ThreadManager
from releaseessentials.managers.report import ReportManager
from releaseessentials.managers.subjects.csv import Csv
from releaseessentials.managers.subjects.csv import CSVClient
from releaseessentials.managers.subjects.csv import CSVFile
from tests.mocks.dataproviders import DataProviders
from releaseessentials.resources import Replacements
from releaseessentials.log import Logger
from releaseessentials.document import DocumentController
from releaseessentials.interface import ReportingInterface

class TestCsvManager(TestCase):
    _test_configuration_path = ''
    _required_root_elements = Configuration._required_root_elements

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        self.tearDown()
        mock_log.return_value = None
        mock_parser.return_value = []
        self.mock_parser = mock_parser
        path = os.path.dirname(os.path.realpath(__file__ + '../../../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        self._mock_log = mock_log

    def tearDown(self):
        Configuration.NAMESPACE = 'releaseessentials'
        if Configuration._instance is not None:
            del Configuration._instance
            Configuration._instance = None
        if Configuration._configuration is not None:
            del Configuration._configuration
            Configuration._configuration = None
        Configuration._required_root_elements = self._required_root_elements
        if Replacements._instance is not None:
            del Replacements._instance
            Replacements._instance = None
        if ThreadManager._instance is not None:
            del ThreadManager._instance
            ThreadManager._instance = None

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @patch('pandas.read_csv')
    def test_csv_with_multi_file(self, mock_dataframe, mock_config_locations, mock_parse):
        mock_config_locations.return_value = [self._path]
        mock_dataframe.side_effect = DataProviders.get_csv_results()
        with patch('releaseessentials.managers.subjects.docx.Docx') as docx:
            docx.__implements__ = (ReportingInterface,)
            document = DocumentController('csv_multi_file.json')
            document.build()
            self.assertEquals(None, document._thread_manager.projectmanager._client.server)
            self.assertIsInstance(document._thread_manager.projectmanager._client.projects(), list)
            csvfiles = document._thread_manager.projectmanager._client._client
            self.assertIsInstance(csvfiles, CSVClient)
            self.assertEquals(len(csvfiles), 2)
            for csv in csvfiles:
                self.assertIsInstance(csv._dataframe, pandas.DataFrame)
                self.assertEquals(len(csv._dataframe.index), 3)

            document.save('Test Document.docx')

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @patch('pandas.read_csv')
    def test_csv_with_single_file(self, mock_dataframe, mock_config_locations, mock_parse):
        self.tearDown()
        mock_config_locations.return_value = [self._path]
        mock_dataframe.side_effect = DataProviders.get_csv_results()
        with patch('releaseessentials.managers.subjects.docx.Docx') as docx:
            docx.__implements__ = (ReportingInterface,)
            document = DocumentController('csv_single_file_distinct.json')
            document.build()
            self.assertEquals(None, document._thread_manager.projectmanager._client.server)
            self.assertIsInstance(document._thread_manager.projectmanager._client.projects(), str)
            csvfiles = document._thread_manager.projectmanager._client._client
            self.assertIsInstance(csvfiles, CSVClient)
            self.assertEquals(len(csvfiles), 1)
            for csv in csvfiles:
                self.assertIsInstance(csv._dataframe, pandas.DataFrame)
                self.assertEquals(len(csv._dataframe.index), 3)

            document.save('Test Document.docx')

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @patch('pandas.read_csv')
    def test_csv_with_broken_file(self, mock_dataframe, mock_config_locations, mock_parse):
        self.tearDown()
        mock_config_locations.return_value = [self._path]
        mock_dataframe.side_effect = DataProviders.get_csv_results()
        with patch('releaseessentials.managers.subjects.docx.Docx') as docx:
            docx.__implements__ = (ReportingInterface,)
            document = DocumentController('broken_csv.json')
            document.build()
            csvfiles = document._thread_manager.projectmanager._client._client
            self.assertIsInstance(csvfiles, CSVClient)
            self.assertEquals(len(csvfiles), 0)

            document.save('Test Document.docx')

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @patch('pandas.read_csv')
    def test_csv_with_multi_file_no_fields(self, mock_dataframe, mock_config_locations, mock_parse):
        self.tearDown()
        mock_config_locations.return_value = [self._path]
        mock_dataframe.side_effect = DataProviders.get_csv_results()
        with patch('releaseessentials.managers.subjects.docx.Docx') as docx:
            docx.__implements__ = (ReportingInterface,)
            document = DocumentController('csv_multi_file_no_fields.json')
            document.build()
            csvfiles = document._thread_manager.projectmanager._client._client
            self.assertIsInstance(csvfiles, CSVClient)
            self.assertEquals(len(csvfiles), 2)
            for csv in csvfiles:
                self.assertIsInstance(csv._dataframe, pandas.DataFrame)
                self.assertEquals(len(csv._dataframe.index), 3)
            document.save('Test Document.docx')

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    @patch('pandas.read_csv')
    def test_csv_with_multi_file_max_results(self, mock_dataframe, mock_config_locations, mock_parse):
        self.tearDown()
        mock_config_locations.return_value = [self._path]
        mock_dataframe.side_effect = DataProviders.get_csv_results()
        with patch('releaseessentials.managers.subjects.docx.Docx') as docx:
            docx.__implements__ = (ReportingInterface,)
            document = DocumentController('csv_multi_file_max_results.json')
            document.build()
            csvfiles = document._thread_manager.projectmanager._client._client
            self.assertIsInstance(csvfiles, CSVClient)
            self.assertEquals(len(csvfiles), 2)
            for csv in csvfiles:
                self.assertIsInstance(csv._dataframe, pandas.DataFrame)
                self.assertEquals(len(csv._dataframe.index), 3)

            document.save('Test Document.docx')

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.configuration.Configuration._get_locations')
    def test_csv_with_no_file(self, mock_config_locations, mock_parse):
        self.tearDown()
        mock_config_locations.return_value = [self._path]
        print(mock_config_locations.return_value)
        with patch('releaseessentials.managers.subjects.docx.Docx') as docx:
            docx.__implements__ = (ReportingInterface,)
            document = DocumentController('csv_single_file_distinct.json')
            document.build()
            csvfiles = document._thread_manager.projectmanager._client._client
            self.assertIsInstance(csvfiles, CSVClient)
            self.assertEquals(len(csvfiles), 0)
