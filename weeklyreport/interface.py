from abc       import ABCMeta, abstractmethod
from threading import Thread

_not_implemented = 'Method must be implemented by a child'

class ViewWindowInterface(metaclass=ABCMeta):
    """
    Interface for creating a view window
    """
    @abstractmethod
    def write(self, message):
        """
        Write the given message to the log

        @param message string
        """
        raise NotImplementedError(_not_implemented)

    @abstractmethod
    def flush(self):
        """
        Flush output to the log window
        """
        raise NotImplementedError(_not_implemented)

    @abstractmethod
    def readline(self):
        """
        Get a line of text from the user

        @param message string

        @return string
        """
        raise NotImplementedError(_not_implemented)

class ManagerInterface(metaclass=ABCMeta):
    """
    Interface class for extending the project managers
    """
    @abstractmethod
    def search_issues(self, search_filter, max_results = False):
        """
        Search for issues within the defined management interface

        @param search_filter A (JQL?) search string to pass to the management interface
        @param max_results If False will pull back all visible issues in batches of 50

        @return list
        """
        raise NotImplementedError(_not_implemented)

    @abstractmethod
    def projects(self):
        """
        return a comprehensive list of visible projects

        @return list
        """
        raise NotImplementedError(_not_implemented)

    @abstractmethod
    def configuration(self):
        """
        Returns a singleton reference to the configuration object
        """
        raise NotImplementedError(_not_implemented)
