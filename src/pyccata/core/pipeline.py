"""
Set up command pipelines for shell execution
"""
from pyccata.core.abstract import ControllerAbstract
from pyccata.core.exceptions import ThreadFailedError
from pyccata.core.configuration import Configuration
from pyccata.core.factory import CommandFactory
from pyccata.core.log import Logger
from pyccata.core.decorators import accepts

class Pipeline(ControllerAbstract):
    """
    Uses the 'pipeline' segment of the json configuration
    to trigger shell commands in a pipeline .
    """
    @property
    def partfactory(self):
        """ get the factory used for creating document parts """
        if self._part_factory is None:
            return CommandFactory()
        return self._part_factory

    def build(self):
        """ Build the report """
        for commands in self.configuration.pipeline:
            self._commands.append(self.partfactory.command(self.threadmanager, command))

        self.threadmanager.start()
        if not self.threadmanager.completed:
            raise ThreadFailedError('Failed to build pipeline due to invalid or incomplete threads')

    @accepts(str)
    def save(self, filename):
        """
        Save the current pipeline

        @param filename string

        Note: Does nothing
        """
        pass
