""" Paragraph module """
from weeklyreport.managers.report import ReportManager
from weeklyreport.abstract import ThreadableDocument
from weeklyreport.decorators import accepts

class Paragraph(ThreadableDocument):
    """ Create a new Paragraph object """
    PRIORITY = 10
    _content = ''
    def setup(self, text=''):
        """ Setup the paragraph """
        # pylint: disable=arguments-differ
        self._content = text

    def run(self):
        """ paragraphs should not do anything during thread execution """
        self._complete = True

    @accepts(ReportManager)
    def render(self, document):
        """ Render the paragraph text """
        document.add_paragraph(self._content)
