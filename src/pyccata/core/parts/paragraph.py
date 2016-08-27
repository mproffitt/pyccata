""" Paragraph module """
from pyccata.core.managers.report import ReportManager
from pyccata.core.abstract import ThreadableDocument
from pyccata.core.decorators import accepts
from pyccata.core.resources  import Replacements
from pyccata.core.log import Logger

class Paragraph(ThreadableDocument):
    """ Create a new Paragraph object """
    PRIORITY = 10
    _content = ''

    @accepts(text=(str, list))
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
        Logger().info('Writing paragraph')
        if isinstance(self._content, str):
            document.add_paragraph(Replacements().replace(self._content))
        else:
            for i, run in enumerate(self._content):
                if i == 0:
                    document.add_paragraph(run)
                elif isinstance(run, str):
                    document.add_run(run)
                else:
                    document.add_run(run.text, style=run.style)
