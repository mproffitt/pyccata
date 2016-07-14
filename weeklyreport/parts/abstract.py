""" class used to parse section abstracts """
from weeklyreport.helpers import read_file
from weeklyreport.decorators import accepts
from weeklyreport.managers.report import ReportManager
from weeklyreport.configuration import Configuration
from weeklyreport.resources  import Replacements

class Abstract(object):
    """ class to parse the abstract """

    # pylint: disable=too-few-public-methods
    # This is a helper class for serving a single
    # purpose. It will probably never have any more
    # methods

    _content = None

    def __init__(self, content):
        """ initialise the object """
        self._content = [line for line in read_file(content, report_path=Configuration().report.datapath).split("\n\n")]

    @accepts(ReportManager)
    def render(self, document):
        """
        Render the text of the abstract into a series of paragraphs

        @param document ReportManager
        """
        for paragraph in self._content:
            document.add_paragraph(Replacements().replace(paragraph))
