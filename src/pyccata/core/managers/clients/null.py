"""
Null Report client

This client is for executions which require no structured output.
"""
import os
from pyccata.core.interface import ReportingInterface
from pyccata.core.decorators import accepts
from pyccata.core.log import Logger
from pyccata.core.parts.list import List
from pyccata.core.configuration import Configuration


class Null(object):
    """
    Null report class
    """
    __implements__ = (ReportingInterface,)
    _client = None
    _configuration = None
    _run = None
    _template_file = None

    REQUIRED = []
    MAXWIDTH = 0

    def __init__(self):
        """ Load the driver and create title page """
        Logger().info('Initialising Null Report Driver driver')
        self._configuration = Configuration()

    @property
    def client(self):
        """ Get the client interface """
        pass

    @accepts(str, style=(None, str))
    def add_paragraph(self, text, style=None):
        """
        Add a paragraph of text to the report

        @param text string
        """
        pass

    @accepts(str, style=(None, str))
    def add_run(self, text, style=None):
        """
        Adds a run of text to the current active paragraph

        @param text string
        @param style str
        """
        pass

    @accepts(str, style=(None, str))
    def add_list(self, text, style=None):
        """
        Add a paragraph of text to the report

        @param text string
        @param style string [ListBullet,ListNumber]
        """
        pass

    @accepts(str, int)
    def add_heading(self, heading, level):
        """
        Add a heading to the report

        @param heading string
        @param level   int
        """
        pass

    @accepts(headings=(None, list), data=(None, list), style=str)
    def add_table(self, headings=None, data=None, style=''):
        """
        Add a table to the report

        @param headings list
        @param data     list   A nested lists of strings.
        @param style    string
        """
        pass

    @accepts(str, width=(int, float))
    def add_picture(self, filename, width=0):
        """
        Add a picture to the report

        @param filename string
        @param width    int
        """
        pass

    def add_page_break(self):
        """ Adds a page break to the report """
        pass

    def format_for_email(self):
        """
        Adds the document contents to a single table cell for display in email
        """
        pass

    @accepts(str)
    def save(self, filename):
        """
        Save the file to disk

        @param filename string
        """
        pass
