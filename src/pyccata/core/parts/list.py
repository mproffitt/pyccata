"""
Helper class for creating lists of items
"""

from pyccata.core.managers.report import ReportManager
from pyccata.core.abstract import ThreadableDocument
from pyccata.core.decorators import accepts
from pyccata.core.exceptions import ArgumentValidationError
from pyccata.core.filter import Filter
from pyccata.core.resources import ResultListItemAbstract
from pyccata.core.resources  import Replacements
from pyccata.core.log import Logger
from pyccata.core.configuration import Configuration

class List(ThreadableDocument):
    """
    Helper class for creating and managing lists
    """
    STYLE_MAPPINGS = {"ordered": "ListNumber", "unordered": "ListBullet"}
    INDENT = 0.25

    _style = ''
    _content = None

    _field = ''

    @accepts(content=(Filter, list, tuple), style=str, field=str)
    def setup(self, content=None, style='unordered', field='description'):
        """ Set up the list object """
        # pylint: disable=arguments-differ
        if not style.lower() in List.STYLE_MAPPINGS.keys():
            raise ArgumentValidationError('style', '__init__', self.STYLE_MAPPINGS.keys(), style)
        self._style = style.lower()
        self._field = field

        if isinstance(content, tuple):
            try:
                content = Filter(
                    content.query,
                    max_results=getattr(content, 'max_results') if hasattr(content, 'max_results') else 0,
                    fields=getattr(content, 'fields') if hasattr(content, 'fields') else None,
                    collate=(content.collate if hasattr(content, 'collate') else None),
                    distinct=(content.distinct if hasattr(content, 'distinct') else False),
                    namespace=Configuration.NAMESPACE
                )
                # pylint: disable=broad-except
                # Any reason can come back here. Just need to
                # log the exception and move on.
            except Exception as exception:
                Logger().warning('Got type tuple but cannot create filter')
                Logger().warning(exception)

        self._content = List._parse(content)
        if isinstance(self._content, Filter):
            Logger().debug('Appending list content filter to thread manager')
            self.threadmanager.append(self._content)
        else:
            for item in self:
                if isinstance(item, Filter):
                    self.threadmanager.append(item)

    def run(self):
        """
            Builds the list and executes any queries.
        """
        while not self._complete:
            if isinstance(self._content, Filter):
                #pylint disable=maybe-no-member
                self._complete = self._content.complete
                if self._content.failed:
                    Logger().debug(self._content.failure)
                    self._complete = True
            else:
                complete = True
                for item in self._content:
                    if isinstance(item, Filter):
                        complete = item.complete or item.failed
                        if item.failed:
                            Logger().warning('Failed to execute \'' + item.query + '\'')
                            Logger().warning(item.failure)
                    if not complete:
                        break
                if complete:
                    self._complete = complete

    @accepts(ReportManager)
    def render(self, document):
        """ Render the paragraph text """
        Logger().info('Writing list {0}'.format(self.title if self.title is not None else ''))
        if self.title is not None:
            document.add_heading(Replacements().replace(self.title), 3)

        # Lists should be unique
        for item in self:
            # Only append the first result, discard any extra
            text = None
            if isinstance(item, str):
                text = item
            elif isinstance(item, ResultListItemAbstract):
                text = getattr(item, self._field) if hasattr(item, self._field) else ''
            elif (
                    isinstance(item.results, list)
                    and len(item.results) == 1
                    and isinstance(item.results[0], ResultListItemAbstract)
            ):
                text = getattr(
                    item.results[0],
                    self._field
                ) if hasattr(item.results[0], self._field) else item.results[0].description
            self._write(document, text)

    @accepts(ReportManager, (list, str, None))
    def _write(self, document, text):
        """ Write text into the document """
        if isinstance(text, list):
            for item in text:
                document.add_list(Replacements().replace(
                    getattr(item, 'value') if isinstance(item, object) and hasattr(item, 'value') else item
                ), style=List.STYLE_MAPPINGS[self._style])
        elif text is not None:
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
