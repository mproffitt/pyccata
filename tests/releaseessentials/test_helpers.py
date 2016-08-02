import os
import shutil
from unittest import TestCase
from mock import call
from mock import patch
from mock import PropertyMock
from ddt import ddt, data, unpack
from collections import namedtuple
from releaseessentials.log import Logger
from tests.mocks.dataproviders import DataProviders
from releaseessentials.helpers import create_directory
from releaseessentials.helpers import unzip
from releaseessentials.helpers import unzip_flat_dir
from releaseessentials.helpers import mkzip

class TestHelpers(TestCase):

    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'mocks'))

    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    def test_makedirs_was_never_called(self, mock_makedirs, mock_exists):
        create_directory('/var/lib/git')
        mock_makedirs.assert_not_called()

    @patch('zipfile.ZipFile.extract')
    def test_unzip_without_flattening_the_structure(self, mock_extract):
        file_list = [
            'etc/',
            'etc/test_create.sql',
            'etc/test_procedure.sql',
            'etc/test_function.sql',
            'etc/test_insert.sql',
            'etc/test_delete.sql',
            '../test.sql'
        ]
        unzip(os.path.join(self._path, 'example.zip'), '/tmp/test_directory')
        self.assertEquals(len(file_list), mock_extract.call_count)

    @patch('builtins.open', create=True)
    def test_unzip_when_flattening_structure(self, mock_extract):
        file_list = [
            'etc/',
            'etc/test_create.sql',
            'etc/test_procedure.sql',
            'etc/test_function.sql',
            'etc/test_insert.sql',
            'etc/test_delete.sql',
            '../test.sql'
        ]

        with patch('shutil.copyfileobj') as mock_copy:
            unzip(os.path.join(self._path, 'example.zip'), '/tmp/test_directory', flatten=True)
            self.assertEquals(len(file_list)-1, mock_copy.call_count)

    @patch('zipfile.ZipFile.write')
    def test_mkzip(self, mock_write):
        path = os.path.join(self._path, 'etc')
        calls = [
            call(os.path.join(path, 'test_create.sql')),
            call(os.path.join(path, 'test_procedure.sql')),
            call(os.path.join(path, 'test_function.sql')),
            call(os.path.join(path, 'test_insert.sql')),
            call(os.path.join(path, 'test_delete.sql'))
        ]
        mkzip(path, os.path.join(self._path, 'testfile.zip'))
