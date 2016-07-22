"""
Helper class for creating lists of items
"""

from weeklyreport.managers.report import ReportManager
from weeklyreport.abstract import ThreadableDocument
from weeklyreport.decorators import accepts
from weeklyreport.exceptions import ArgumentValidationError
from weeklyreport.filter import Filter
from weeklyreport.resources import Issue
from weeklyreport.resources  import Replacements
from weeklyreport.log import Logger

class List(ThreadableDocument):
    """
    Helper class for creating and managing lists
    """
    STYLE_MAPPINGS = {"ordered": "ListNumber", "unordered": "ListBullet"}
    INDENT = 0.25

    _style = ''
    _content = None

    _field = ''

    @accepts(content=(Filter, list), style=str, field=str)
    def setup(self, content=None, style='unordered', field='description'):
        """ Set up the list object """
        # pylint: disable=arguments-differ
        if not style in List.STYLE_MAPPINGS.keys():
            raise ArgumentValidationError('style', '__init__', self.STYLE_MAPPINGS.keys(), style)
        self._style = style
        self._field = field

        self._content = List._parse(content)

        if isinstance(self._content, Filter):
            self.threadmanager.append(self._content)
        else:
            for item in self:
                if isinstance(item, Filter):
                    self.threadmanager.append(item)

    def run(self):
        """
            Builds the list and executes any queries.
        """
        while not self.complete:
            if isinstance(self._content, Filter):
                #pylint disable=maybe-no-member
                self._complete = self._content.complete
            else:
                for item in self._content:
                    if isinstance(item, Filter) and item.failed:
                        Logger().warning('Failed to execute \'' + item.query + '\'')
                        Logger().warning('Reason was:')
                        Logger().warning(item.failure)
                self._complete = True

    @accepts(ReportManager)
    def render(self, document):
        """ Render the paragraph text """

        for item in self:
            # Only append the first result, discard any extra
            text = None
            if isinstance(item, str):
                text = item
            elif isinstance(item, Issue):
                text = item.description
            elif isinstance(item.results, list) and len(item.results) == 1 and isinstance(item.results[0], Issue):
                text = item.results[0].description

            if text is not None:
                document.add_list(Replacements().replace(text), style=List.STYLE_MAPPINGS[self._style])

    @staticmethod
    @accepts((Filter, list))
    def _parse(content):
        """ Parse the current content object """
        if isinstance(content, Filter):
            return content

        actual = []
        for item in content:
            for object_type in (str, int, Filter):
                if isinstance(item, object_type):
                    actual.append(item)
        return actual


    # =============================================
    # Magic methods for creating iterable object
    #

    def __getitem__(self, key):
        if isinstance(self._content, Filter):
            return self._content.results.__getitem__(key)
        return self._content.__getitem__(key)

    def __setitem__(self, key, value):
        if isinstance(self._content, Filter):
            return self._content.results.__setitem__(key, value)
        return self._content.__setitem__(key, value)

    def __len__(self):
        if isinstance(self._content, Filter):
            return self._content.results.__len__()
        return self._content.__len__()

    def __delitem__(self, key):
        if isinstance(self._content, Filter):
            return self._content.results.__delitem__(key)
        return self._content.__delitem__(key)

    def __iter__(self):
        if isinstance(self._content, Filter):
            return self._content.results.__iter__()
        return self._content.__iter__()

    def __reversed__(self):
        if isinstance(self._content, Filter):
            return self._content.results.__reversed__()
        return self._content.__reversed__()

    def __contains__(self, item):
        if isinstance(self._content, Filter):
            return self._content.results.__contains__(item)
        return self._content.__contains__(item)
