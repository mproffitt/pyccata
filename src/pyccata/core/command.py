"""
Create threadable calls to the shell

@package pyccata.core
@author Martin Proffitt <mproffitt@jitsc.co.uk>
@link http://
"""
import os
import re
import shlex
from subprocess import Popen
from pyccata.core.log import Logger
from pyccata.core.decorators import accepts
from pyccata.core.threading import Threadable
from pyccata.core.resources import Command
from pyccata.core.resources import Redirect
from pyccata.core.configuration import Configuration
from pyccata.core.managers.thread import ThreadManager
from pyccata.core.filter import Filter
from pyccata.core.exceptions import ThreadFailedError
from pyccata.core.resources import ResultList
from pyccata.core.resources import CommandLineResultItem
from pyccata.core.resources import Replacements
from pyccata.core.exceptions import InvalidModuleError
from pyccata.core.helpers import include

class ThreadableCommand(Threadable):
    """
    This class can be used to process shell commands
    """
    # pylint: disable=too-many-instance-attributes,too-many-public-methods
    # It is understood that this class requires a number of attributes and
    # accessor methods.

    MAX_PRIORITY = 10000
    PRIORITY = 0
    _redirect_regex = None
    _commands = None
    _redirects = None

    PRIORITY = 1000
    _results = None

    @property
    def results(self):
        return self._results

    @property
    def threadmanager(self):
        """ Get the current loaded threadmanager """
        return self._thread_manager

    @accepts(ThreadManager, tuple, append=bool)
    def __init__(self, threadmanager, config, append=True):
        """
        Initialise the ThreadableCommand object
        """
        self._thread_manager = threadmanager
        self._commands = []
        self._observers = []
        self._redirects = []
        self._results = ResultList()

        # pylint: disable=protected-access
        # verification that Configuration is not initialised and initialise it
        # with the thread manager - this is desired behaviour against the singleton
        # to prevent it being loaded multiple times inside threading objects

        if Configuration._instance is None:
            Configuration._instance = self.threadmanager.configuration
        self.validate_setup(config)

        super().__init__(**config._asdict())
        if append:
            self.threadmanager.append(self)

    @accepts(
        name=str,
        command=str,
        input_directory=(None, str),
        output_directory=(None, str),
        wait_for=(None, str, Threadable)
    )
    def setup(self, name='', command='', input_directory=None, output_directory=None, wait_for=None):
        """
        Sets up the thread and builds the command structure.

        @param name            string
        @param command          string
        @param input_directory  string or None
        @param output_directory string or None
        @param wait_for         string, None or ThreadableCommand

        If this method is overridden, the overriding method must call back up to parent
        or implement this functionality directly. Failure to do this will prevent the thread
        from executing.

        The flag `wait_for` will prevent the thread from executing until the wait_for thread
        has completed. This is useful in the event a command needs the complete output from
        another thread before it can work, for example, downloading data then parsing it.

        If `wait_for` is None, the thread will execute as soon as there is room in the pool.
        (Default pool size = ThreadManager.POOL_SIZE).
        """
        # pylint: disable=arguments-differ
        # This method provides specific implementations of *args and **kwargs

        # pylint: disable=too-many-arguments
        # This method requires a larger number of arguments than the standard
        self.thread_name = name
        self._input_directory = Replacements().replace(input_directory)
        self._output_directory = Replacements().replace(
            output_directory,
            additional=self.replacements(output_directory)
        )

        self._build_command(command)

    @accepts(str)
    def _build_command(self, command_string):
        """
        Breaks down a command string and returns a list of commands initialised for subprocess.Popen

        @param command_string string
        """
        command_list = command_string.split(' | ')
        for command_structure in command_list:
            command = Command()
            redirect_regex = re.compile(
                r"(?P<command>.*?)( ((?P<redirect>[&\d]?)>+ ?&?(?P<filename>\S+)))( ?< ?(?P<infile>.*))?",
                re.DOTALL
            )

            matches = [match.groupdict() for match in redirect_regex.finditer(command_structure)]
            if len(matches) == 0:
                try:
                    structure = shlex.split(command_structure)
                except ValueError as exception:
                    Logger().error('Failed to parse command \'' + command_structure + '\'')
                    raise

                command.command = structure[0]
                command.arguments = structure[1:]
            else:
                try:
                    structure = shlex.split(matches[0]['command'])
                except ValueError as exception:
                    Logger().error('Failed to parse command \'' + matches[0]['command'] + '\'')
                    raise exception
                command.command = structure[0]
                command.arguments = structure[1:]
                for match in matches:
                    command.redirects.append(
                        Redirect(
                            redirect_input=(
                                int(match['redirect']) if match['redirect'].isdigit() else match['redirect']
                            ),
                            redirect_output=int(match['filename']) if match['filename'].isdigit() else match['filename']
                        )
                    )
            self._commands.append(command)

    def run(self):
        """
        Executes the current thread
        """
        processes = []
        for command in self._commands:
            last_pipe = processes[-1].stdout if len(processes) > 0 else None
            processes.append(
                Popen(
                    [command.command] + command.arguments,
                    stdin=last_pipe,
                    stdout=command.stdout,
                    stderr=command.stderr
                )
            )
            command.return_code = processes[-1].poll()

        if processes[-1].stdout is not None and hasattr(processes[-1].stdout, 'readline'):
            for line in iter(processes[-1].stdout.readline, b''):
                item = CommandLineResultItem()
                item.line = line.decode('utf8').strip()
                self._results.append(item)

        stderr = []
        if processes[-1].stderr is not None:
            for line in iter(processes[-1].stderr.readline, b''):
                stderr.append(line.decode('utf8').strip())
        processes[-1].communicate()
        if len(stderr) != 0:
            self.failure = ThreadFailedError(stderr)
        self._complete = True

    def replacements(self, string_to_search):
        """
        Compiles a list of optional string replacements for command thread strings
        """
        replacements = {}
        function_regex = re.compile(
            r'.*?[-_.]{1}\{(?P<what>.*?)\.(?P<command>.*?)\}',
            re.DOTALL
        )
        matches = [match.groupdict() for match in function_regex.finditer(string_to_search)]
        if len(matches) == 0:
            return None

        for match in matches:
            string = '{0}.{1}'.format(match['what'], match['command'])
            what = match['what']
            if Replacements().find(what.upper()):
                what = Replacements().replace('{' + what.upper() + '}')
            command = '{0}_helper'.format(match['command'])
            try:
                command = include(command, 'pyccata', 'helpers')
            except InvalidModuleError:
                Logger().error(
                    'Invalid helper method {0} specified for {1}'.format(
                        match['command'],
                        string
                    )
                )
                raise
            replacements[string] = command(what)
        return replacements

    @staticmethod
    def logdir():
        """ Get a log directory for the command output """
        path = os.path.join(Replacements().replace('{BASE_PATH}'), 'log')
        if not os.path.exists(path):
            os.makedirs(path)
        return path
