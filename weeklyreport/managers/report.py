"""
Defines the Reporting manager used by the application
"""

from weeklyreport.manager import Manager
from weeklyreport.decorators import accepts
from weeklyreport.interface import ReportingInterface
from weeklyreport.helpers import read_file

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

    def __init__(self):
        """
        Initialise the object and call _load
        """
        namespace = self.configuration.NAMESPACE
        self._load(namespace, self.configuration.reporting, must_implement=ReportingInterface)
        self._maxwidth = self.client.MAXWIDTH
        self.create_title_page()

    @property
    def maxwidth(self):
        """ Get the maximum width of the document """
        return self._maxwidth

    def create_title_page(self):
        """ Creates a title page for the report using settings from configuration """
        self.add_heading(self.configuration.report.title, 0)
        self.add_heading(self.configuration.report.subtitle, 1)
        for paragraph in read_file(self.configuration.report.abstract).split("\n"):
            self.add_paragraph(paragraph)



    @accepts(str)
    def add_paragraph(self, text):
        """
        Add a paragraph of text to the report

        @param text string
        """
        self.client.add_paragraph(text)

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

    @accepts(str)
    def save(self, filename):
        """
        Save the file to disk

        @param filename string
        """
        self.client.save(filename)

