"""
Defines the interfaces used by the weeklyreport package
"""
from abc import ABCMeta
from abc import abstractmethod

# Disabled because these are all pure interfaces
# and not abstract classes. Pylint is incorrectly
# reading these as being abstract base classes.

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
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def flush(self):
        """
        Flush output to the log window
        """
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def readline(self):
        """
        Get a line of text from the user

        @return string
        """
        raise NotImplementedError('Method must be implemented by a child')

class ManagerInterface(metaclass=ABCMeta):
    """
    Interface class for extending the project managers
    """

    @abstractmethod
    def search_issues(self, search_filter, max_results=False, fields=list):
        """
        Search for issues within the defined management interface

        @param search_filter A (JQL?) search string to pass to the management interface
        @param max_results If False will pull back all visible issues in batches of 50

        @return list
        """
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def projects(self):
        """
        return a comprehensive list of visible projects

        @return list
        """
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def configuration(self):
        """
        Returns a singleton reference to the configuration object
        """
        raise NotImplementedError('Method must be implemented by a child')

class ObservableInterface(metaclass=ABCMeta):
    """
    Interface for Observable objects
    """

    @abstractmethod
    def append(self, observer):
        """
        Adds an observer to the list of objects observing this one.

        @param observer Observable
        """
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def notify(self, results):
        """
        Iterates over the observables and notifies them of the results.

        @param results [False|ResultSet] If a ResultSet is provided, the current
                                         objects results are updated. If False (default),
                                         calls notify on all observing objects
        """
        raise NotImplementedError('Method must be implemented by a child')

class ReportingInterface(metaclass=ABCMeta):
    """
    Interface for implementing Report rendering types
    """

    @abstractmethod
    def add_paragraph(self, text):
        """
        Add a paragraph of text to the report

        @param text string
        """
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def add_heading(self, heading, level):
        """
        Add a heading to the report

        @param heading string
        @param level   int
        """
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def add_table(self, headings=None, data=None, style=''):
        """
        Add a table to the report

        @param rows  int
        @param cols  int
        @param style string
        @param data  list
        """
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def add_picture(self, filename, width=0):
        """
        Add a picture to the report

        @param filename string
        @param width    int
        """
        raise NotImplementedError('Method must be implemented by a child')

    @abstractmethod
    def add_page_break(self):
        """ Adds a page break to the report """
        raise NotImplementedError('Method must be implemented by a child')

