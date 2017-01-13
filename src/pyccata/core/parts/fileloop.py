"""
Loops over all files in a directory and performs a command over each
"""
import os
import sys
import re
import fnmatch
import time
from collections import namedtuple

from pyccata.core.threading import Threadable
from pyccata.core.resources import Replacements
from pyccata.core.command import ThreadableCommand

class Fileloop(ThreadableCommand):
    """
    """
    _input_directory = ''
    _output_directory = ''
    _input_pattern = ''
    _strip = ''

    _maxthreads = 1
    _wait_for = None

    def setup(
            self, name,
            command='',
            input_directory='',
            output_directory='',
            input_pattern='*',
            strip='',
            output_extension='',
            maxthreads=1,
            wait_for=None
    ):
        self.thread_name = name
        self._command = command
        self._input_directory = Replacements().replace(input_directory)
        self._output_directory = Replacements().replace(
            output_directory,
            additional=self.replacements(output_directory)
        )
        self._strip = strip
        self._input_pattern = input_pattern
        self._output_extension = output_extension
        self._maxthreads = maxthreads
        self._wait_for = None
        if wait_for is not None:
            self._wait_for = self.threadmanager.find(wait_for)

    def _build_command_list(self):
        """
        Builds the current command set, one for each file
        """
        files = [
            os.path.join(self._input_directory, filename)
            for filename in os.listdir(self._input_directory)
            if os.path.isfile(os.path.join(self._input_directory, filename))
                and fnmatch.fnmatch(filename, self._input_pattern)
        ]

        config = namedtuple('config', 'name command input_directory output_directory wait_for')
        for index, filename in enumerate(files):
            additional={}
            additional['filename'] = filename
            output_file, current_extension = os.path.splitext(filename)

            if self._strip != '' and self._output_extension == '':
                self._output_extension = self._current_extension
            if self._strip == '' and self._output_extension != '':
                self._strip = '.' + self._current_extension

            if self._strip != '':
                output_file = os.path.basename(filename)
                output_file = re.sub(r'{0}'.format(self._strip), '', output_file)

            if self._output_extension != '':
                output_file = output_file + '.' + self._output_extension

            additional['output'] = os.path.join(self._output_directory, output_file)
            additional['logfile'] = os.path.join(ThreadableCommand.logdir(), '{0}.log'.format(self.thread_name))

            command_string = Replacements().replace(self._command, additional=additional)
            self._commands.append(
                ThreadableCommand(
                    self._thread_manager,
                    config(
                        name='{0}-{1}'.format(self._name, index),
                        command=command_string,
                        input_directory=self._input_directory,
                        output_directory=self._output_directory,
                        wait_for=None
                    )
                )
            )

    def run(self):
        """ Run the current set of commands """
        if self._wait_for is not None:
            while not self._wait_for.complete:
                time.sleep(Threadable.THREAD_SLEEP)
        self._build_command_list()
        if not os.path.exists(self._output_directory):
            os.makedirs(self._output_directory)

        pool = []
        current_index = 0
        for command in self._commands:
            if current_index < self._maxthreads:
                pool.append(command)
                self.threadmanager.append(pool[-1])
                current_index += 1

            if current_index == self._maxthreads:
                while True:
                    for item in pool:
                        if item.complete:
                            current_index -= 1
                    if current_index < self._maxthreads:
                        break
                    time.sleep(Threadable.THREAD_SLEEP)
        self._complete = True
