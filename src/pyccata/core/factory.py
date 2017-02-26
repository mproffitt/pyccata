"""
Contains Factory classes for loading different sections

Each class under this module should extend FactoryAbstract
"""
from pyccata.core.abstract import FactoryAbstract
from pyccata.core.abstract import ThreadableDocument
from pyccata.core.command import ThreadableCommand

class DocumentPartFactory(FactoryAbstract):
    """
    Factory for loading document parts
    """
    @property
    def allowed_class(self):
        """
        Gets the type of object allowed within this class
        """
        return ThreadableDocument

    def __new__(cls):
        # children are always allowed to call their parents properties
        # pylint: disable=protected-access
        if cls._instance is None:
            cls._is_loaded = False
            cls._instance = super(DocumentPartFactory, cls).__new__(cls)
        return cls._instance

class CommandFactory(FactoryAbstract):
    """
    Factory for loading system commands within a threadable shell
    """

    @property
    def allowed_class(self):
        """
        Gets the type of class allowed within this factory
        """
        return ThreadableCommand

    def __new__(cls):
        # children are always allowed to call their parents properties
        # pylint: disable=protected-access
        if cls._instance is None:
            cls._is_loaded = False
            cls._instance = super(CommandFactory, cls).__new__(cls)
        return cls._instance

    def command(self, name):
        """
        Get a command from the factory

        :param string: name
        :returns: Command

        """
        return getattr(self, name)
