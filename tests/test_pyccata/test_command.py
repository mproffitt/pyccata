import os
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

from tests.mocks.dataproviders import DataProviders

@ddt
class TestThreadableCommand(TestCase):

    @patch('pyccata.core.log.Logger.log')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def setUp(self, mock_config, mock_parser, mock_log):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        mock_config.return_value = [self._path]
        mock_parser.return_value = []
        mock_log.return_value = None
        Logger._instance = mock_log
        Configuration(filename='config_sections.json')
        self._thread_manager = ThreadManager()

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'pyccata.core'
        self._thread_manager.clear()
        self._thread_manager._instance = None
        del self._thread_manager

    @data(
        [
            "sed 's/24/25/g'",
            {
                'command':'sed',
                'args':['s/24/25/g']
            }
        ],
        [
            "sed 's/24/25/g' &>/dev/null",
            {
                'command':'sed',
                'args':['s/24/25/g'],
                'redirects': {'0': '/dev/null', '2':'/dev/null'}
            }
        ],
        [
            "sed 's/24/25/g' 1>&2",
            {
                'command':'sed',
                'args':['s/24/25/g'],
                'redirects': {'0':'1'}
            }
        ],
        [
            "sed 's/24/25/g' 2>&1 1>/dev/null",
            {
                'command':'sed',
                'args':['s/24/25/g'],
                'redirects': {'0': '/dev/null', '1':'0'}
            }
        ],
        [
            "sed 's/24/25/g' &>/dev/null < infile.txt",
            {
                'command':'sed',
                'args':['s/24/25/g'],
                'redirects': {'0': '/dev/null', '1':'/dev/null'}
            }
        ],
        [
            "grep -rin --col 'i < 24\|b>19' > /dev/null",
            {
                'command':'grep',
                'args':['-rin', '--col', 'i < 24\|b>19'],
                'redirects': {'0': '/dev/null'}
            }
        ],
        [
            "grep -rin --col 'i < 24\|b>19' 3>/dev/null",
            {
                'command':'grep',
                'args':['-rin', '--col', 'i < 24\|b>19'],
                'redirects': {'0': '0'}
            }
        ],
        [
            "grep -rin --col 'i < 24\|b>19' 3>4",
            {
                'command':'grep',
                'args':['-rin', '--col', 'i < 24\|b>19'],
                'redirects': {'0': '0'}
            }
        ]

    )
    @unpack
    def test_build_command_with_simple_commands(self, command, expected_return):
        configuration = namedtuple('Config', 'title command input_directory output_directory wait_for')
        config = configuration(
            title='Test command',
            command=command,
            input_directory='/tmp',
            output_directory='/tmp',
            wait_for=None
        )
        threadable = ThreadableCommand(self._thread_manager, config)
        commands = threadable._commands
        for command in commands:
            self.assertEquals(command.command, expected_return['command'])
            self.assertEquals(command.arguments, expected_return['args'])
            if not 'redirects' in expected_return.keys():
                continue
            for key in expected_return['redirects'].keys():
                for redirect in command.redirects:
                    if str(redirect.redirect_input) == str(int(key)-1):
                        out = redirect.redirect_output if isinstance(redirect.redirect_output, str) else str(redirect.redirect_output)
                        self.assertEquals(out, expected_return['redirects'][key])
    @data(
        "sed 's/24/25/g",
        "sed 's/24/ > /g' &>/dev/null"
    )
    def test_build_command_raises_error_if_command_wont_parse(self, command):
        configuration = namedtuple('Config', 'title command input_directory output_directory wait_for')
        config = configuration(
            title='Test command',
            command=command,
            input_directory='/tmp',
            output_directory='/tmp',
            wait_for=None
        )
        with self.assertRaises(ValueError):
            threadable = ThreadableCommand(self._thread_manager, config)

    def test_build_command_assigns_observer_to_threadable(self):
        configuration = namedtuple('Config', 'title command input_directory output_directory wait_for')
        config_observing = configuration(
            title='Observing',
            command="sed 's/24/25/g'",
            input_directory='/tmp',
            output_directory='/tmp',
            wait_for=None
        )
        observing = ThreadableCommand(self._thread_manager, config_observing)

        config_observer = configuration(
            title='Observer',
            command="grep -rin --col 'bobjones'",
            input_directory='/tmp',
            output_directory='/tmp',
            wait_for=observing
        )
        observer = ThreadableCommand(self._thread_manager, config_observer)

        self.assertTrue(observing.hasobservers)
        self.assertEquals(1, len(observing.observers))

    def test_run_method_forms_a_pipe_and_reads_output(self):
        configuration = namedtuple('Config', 'title command input_directory output_directory wait_for')
        config = configuration(
            title='GrepForTestsAndReplaceWithBuild',
            command="grep -rin --col 'def test_*' tests | sed 's/test/build/g'",
            input_directory=os.getcwd(),
            output_directory='/tmp',
            wait_for=None
        )
        thread = ThreadableCommand(self._thread_manager, config)
        self._thread_manager.append(thread)
        self._thread_manager.execute()
        self.assertGreater(len(thread.results), 0)

    def test_run_with_redirect(self):
        configuration = namedtuple('Config', 'title command input_directory output_directory wait_for')
        config = configuration(
            title='GrepForTestsAndReplaceWithBuild',
            command="grep 2>&1",
            input_directory=os.getcwd(),
            output_directory='/tmp',
            wait_for=None
        )
        thread = ThreadableCommand(self._thread_manager, config)
        self._thread_manager.append(thread)
        self._thread_manager.execute()
        self.assertGreater(len(thread.results), 0)

    def test_run_raises_error_on_stderr(self):
        configuration = namedtuple('Config', 'title command input_directory output_directory wait_for')
        config = configuration(
            title='GrepForTestsAndReplaceWithBuild',
            command="grep",
            input_directory=os.getcwd(),
            output_directory='/tmp',
            wait_for=None
        )
        thread = ThreadableCommand(self._thread_manager, config)
        self._thread_manager.append(thread)
        with self.assertRaises(ThreadFailedError):
            self._thread_manager.execute()

    @patch('builtins.open', create=True)
    @data(
        "grep -rin --col 'def test_*' tests | sed 's/test/build/g' 1>/tmp/test",
        "grep -rin --col 'def test_*' tests | sed 's/test/build/g' &>/tmp/test",
        "grep -rin --col 'def test_*' tests | sed 's/test/build/g' 2>/tmp/test",
        "grep -rin --col 'def test_*' tests | sed 's/test/build/g' 2>/tmp/test 1>&2"
    )
    def test_run_with_redirect_to_file(self, command, mock_open):
        mock_open.return_value = None
        configuration = namedtuple('Config', 'title command input_directory output_directory wait_for')
        config = configuration(
            title='GrepForTestsAndReplaceWithBuild',
            command=command,
            input_directory=os.getcwd(),
            output_directory='/tmp',
            wait_for=None
        )
        Configuration._instance = None
        thread = ThreadableCommand(self._thread_manager, config)
        self._thread_manager.append(thread)
        self._thread_manager.execute()
        if (len(thread._commands[1].redirects) == 2):
            self.assertEquals(thread._commands[1].stdout, thread._commands[1].stderr)
        self.assertGreater(mock_open.call_count, 0)
        mock_open.assert_called_with('/tmp/test', mode='a')
