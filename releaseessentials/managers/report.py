"""
Defines the Reporting manager used by the application
"""
from collections import namedtuple
from releaseessentials.manager import Manager
from releaseessentials.decorators import accepts
from releaseessentials.interface import ReportingInterface
from releaseessentials.helpers import read_file
from releaseessentials.resources  import Replacements

class ReportManager(Manager):
    """
    The ReportManager takes the ``reporting`` property from
    the configuration root and loads the respective interface
    from the managers/subjects directory

    Interfaces loaded by this application must implement the
    ``ReportingInterface`` interface to be recognised as a viable
    report mechanism.

    Default provided = docx
    """
    __implements__ = (ReportingInterface,)

    REQUIRED = [
        'path',
        'datapath',
        'title',
        'subtitle',
        'abstract',
        'sections'
    ]

    _callbacks = []

    def __init__(self):
        """
        Initialise the object and call _load
        """
        namespace = self.configuration.NAMESPACE
        self._load(namespace, self.configuration.reporting, must_implement=ReportingInterface)
        self._maxwidth = self.client.MAXWIDTH

    def add_callback(self, name, function):
        """
        Adds a callback function for processing reports

        @param name string
        @param function Name of a static method to call back onto.
        """
        for index, callback in enumerate(self._callbacks):
            if callback.name == name:
                self._callbacks[index] = callback._replace(function=function)

        callback = namedtuple('Callback', 'name function')
        self._callbacks.append(callback(name=name, function=function))

    def get_callback(self, name):
        """
        Gets the callback defined for a given name or None

        @param name string
        """
        for item in self._callbacks:
            if item.name == name:
                return item.function
        return None

    @property
    def maxwidth(self):
        """ Get the maximum width of the document """
        return self._maxwidth

    def create_title_page(self):
        """ Creates a title page for the report using settings from configuration """
        self.add_heading(Replacements().replace(self.configuration.report.title), 0)
        self.add_heading(Replacements().replace(self.configuration.report.subtitle), 1)
        for paragraph in read_file(self.configuration.report.abstract).split("\n"):
            self.add_paragraph(Replacements().replace(paragraph))

    @accepts(str, style=(None, str))
    def add_paragraph(self, text, style=None):
        """
        Add a paragraph of text to the report

        @param text string
        @param style string [ListBullet, ListNumber]
        """
        self.client.add_paragraph(text, style=style)


    @accepts(str, style=(None, str))
    def add_run(self, text, style=None):
        """
        Adds a text run to the current active paragraph

        @param text string
        @param style string
        """
        self.client.add_run(text, style=style)

    @accepts(str, style=(None, str))
    def add_list(self, text, style=None):
        """
        Adds an item as a list item in the report

        @param text  string
        @param style string [ListBullet, ListNumber]
        """
        self._client.add_list(text, style=style)

    @accepts(str, int)
    def add_heading(self, heading, level):
        """
        Add a heading to the report

        @param heading string
        @param level   int
        """
        self.client.add_heading(heading, level)

    @accepts(headings=(None, list), data=(None, list), style=str)
    def add_table(self, headings=None, data=None, style=''):
        """
        Add a table to the report

        @param rows  int
        @param cols  int
        @param style string
        @param data  list
        """
        self.client.add_table(headings=headings, data=data, style=style)

    @accepts(str, width=(int, float))
    def add_picture(self, filename, width=0):
        """
        Add a picture to the report

        @param filename string
        @param width    int
        """
        self.client.add_picture(filename, width=width)

    def add_page_break(self):
        """ Adds a page break to the report """
        self._client.add_page_break()

    def format_for_email(self):
        """
        Adds the document contents to a single table cell for display in email
        """
        self._client.format_for_email()


    @accepts(str)
    def save(self, filename):
        """
        Save the file to disk

        @param filename string
        """
        self.client.save(filename)
