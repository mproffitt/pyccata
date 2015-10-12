from abc       import ABCMeta, abstractmethod
from threading import Thread

_not_implemented = 'Method must be implemented by a child'

class ViewWindowInterface(metaclass=ABCMeta):
    """
    Interface for creating a view window
    """
    @abstractmethod
    def write(self):
        raise NotImplementedError(_not_implemented)

    @abstractmethod
    def flush(self):
        raise NotImplementedError(_not_implemented)

    @abstractmethod
    def readline(self):
        raise NotImplementedError(_not_implemented)

class ManagerInterface(metaclass=ABCMeta):
    """
    Interface class for extending the project managers
    """
    pass
