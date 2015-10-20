""" Wrapper onto python-docx library """
from docx import Document
from weeklyreport.interface import ReportingInterface
from weeklyreport.decorators import accepts
from weeklyreport.log import Logger

class Docx(object):
    """ Class for creating reports in Microsoft Word format """
    __implements__ = (ReportingInterface,)
    _client = None
    _configuration = None

    MAXWIDTH = 5.7

    def __init__(self):
        """ Load the driver and create title page """
        Logger().info('Initialising Microsoft Word format driver')

    @property
    def client(self):
        """ Get the client interface """
        if self._client is None:
            self._client = Document()
        return self._client

    @accepts(str)
    def add_paragraph(self, text):
        """
        Add a paragraph of text to the report

        @param text string
        """
        self.client.add_paragraph(str(text))

    @accepts(str, int)
    def add_heading(self, heading, level):
        """
        Add a heading to the report

        @param heading string
        @param level   int
        """
        self.client.add_heading(str(heading), int(level))

    @accepts(headings=(None, list), data=(None, list), style=str)
    def add_table(self, headings=None, data=None, style=''):
        """
        Add a table to the report

        @param headings list
        @param data     list   A nested lists of strings.
        @param style    string
        """
        table = self.client.add_table(rows=1, cols=len(headings), style=style)
        header_cells = table.rows[0].cells
        for i, heading in enumerate(headings):
            header_cells[i].text = str(heading)

        for row in data:
            cells = table.add_row().cells
            for i, col in enumerate(row):
                cells[i].text = str(col)


    @accepts(str, width=int)
    def add_picture(self, filename, width=0):
        """
        Add a picture to the report

        @param filename string
        @param width    int
        """
        if width == 0:
            width = self.MAXWIDTH
        self.client.add_picture(filename, width=width)

    def add_page_break(self):
        """ Adds a page break to the report """
        self.client.add_page_break()

    @accepts(str)
    def save(self, filename):
        """
        Save the file to disk

        @param filename string
        """
        self.client.save(filename)

