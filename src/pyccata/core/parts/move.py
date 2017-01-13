"""
Command for moving a directory
"""
import os
import re
import shutil

from pyccata.core.decorators import accepts
from pyccata.core.command import ThreadableCommand
from pyccata.core.resources import Replacements
from pyccata.core.helpers import include
from pyccata.core.exceptions import InvalidModuleError
from pyccata.core.log import Logger

class Move(ThreadableCommand):
    """
    Moves a directory or file from one location to another
    """
    _input_name = ''
    _output_name = ''
    _recreate = False

    @accepts(
        name=str,
        input_name=str,
        output_name=str,
        recreate=bool
    )
    def setup(self, name, input_name, output_name, recreate=False):
        self.thread_name = name
        self._input_name = Replacements().replace(input_name, additional=self.replacements(input_name))
        self._output_name = Replacements().replace(output_name, additional=self.replacements(output_name))
        self._recreate = recreate

    def run(self):
        """
        Moves the file/directory in a threadable manner
        """
        shutil.move(self._input_name, self._output_name)
        if self._recreate:
            if os.path.isdir(self._output_name):
                os.makedirs(self._input_name)
            elif os.path.isfile(self._output_name):
                open(self._input_name, 'a').close()
        self._complete = True

