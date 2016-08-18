""" class used to parse section abstracts """
from releaseessentials.helpers import read_file
from releaseessentials.decorators import accepts
from releaseessentials.managers.report import ReportManager
from releaseessentials.configuration import Configuration
from releaseessentials.resources  import Replacements
from releaseessentials.log import Logger

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
        Logger().info('Adding section abstract')
        for paragraph in self._content:
            document.add_paragraph(Replacements().replace(paragraph))
