"""
Module for loading document parts
"""
import os
import sys
import inspect
import importlib
from collections import namedtuple
from releaseessentials.abstract import ThreadableDocument
from releaseessentials.configuration import Configuration
from releaseessentials.exceptions import InvalidModuleError
from releaseessentials.exceptions import InvalidClassError

class DocumentPartFactory(list):
    """
    The part factory provides methods of getting the
    different document sections used by the application.

    Valid document parts are stored inside the parts
    module and extend ThreadableDocument as being their
    primary base class. This helps ensure all parts can
    be built correctly and utilise threads where possible.

    If your part does not require threading, add an empty
    ``run`` method

    ThreadableDocument parts must not provide their own
    __init__ method unless super().__init__ is called.

    Instead, ThreadableDocument.__init__ calls back onto
    a ``setup`` method which should be defined within your
    class

    Example:

        class MyDocumentPart(ThreadableDocument):
            def setup(self, *args, **kwargs):
                # do something here...

            def run(self):
                pass

            @accepts(ReportManager):
            def render(self, reportmanager)
                # render part
    """

    MODULE = 'parts'
    _instance = None
    _is_loaded = False
    _allowed = None

    def __init__(self):
        """
        Load all ThreadableDocument extensions under [Configuration.NAMESPACE].parts

        @raise InvalidModuleError if the parts module cannot be found or loaded
        """
        if self._is_loaded:
            return

        self._allowed = [
            'abstract'
        ]

        super().__init__()
        part_loader = namedtuple('PartLoader', 'name cls')
        try:
            module_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), self.MODULE)
            files = [f for f in os.listdir(module_path) if os.path.isfile(os.path.join(module_path, f))]
        except FileNotFoundError:
            raise InvalidModuleError(self.MODULE, Configuration.NAMESPACE)

        clsnames = None
        for filename in files:
            module = os.path.splitext(filename)[0]
            module_name = Configuration.NAMESPACE + '.' + self.MODULE + '.' + module
            try:
                importlib.import_module(module_name)
            except ImportError:
                raise InvalidModuleError(self.MODULE, Configuration.NAMESPACE)
            clsnames = inspect.getmembers(sys.modules[module_name], inspect.isclass)
            for item in clsnames:
                name = item[0].lower()
                cls = item[1]
                if (cls.__module__ == module_name and (
                        issubclass(cls, ThreadableDocument)
                        or module in self._allowed)):
                    self.append(part_loader(name=name, cls=cls))
        self._is_loaded = True

    def __getattr__(self, name):
        for item in self:
            if item.name == name:
                return item.cls
        raise InvalidClassError(name, Configuration.NAMESPACE + '.' + self.MODULE)

    def __new__(cls):
        if cls._instance is None:
            cls._is_loaded = False
            cls._instance = super(DocumentPartFactory, cls).__new__(cls)
        return cls._instance
