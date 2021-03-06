from unittest import TestCase
from mock import patch

from pyccata.core.filter import Filter
from pyccata.core.managers.query import QueryManager
from pyccata.core.log import Logger

class TestQueryManager(TestCase):

    @patch('pyccata.core.configuration.Configuration._parse_flags')
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        Logger._instance = mock_log
        self._manager = QueryManager()

    def tearDown(self):
        self._manager = None

    def test_append_appends_observer_when_queries_match(self):
        mock_filter = Filter('assignee = "Bob"')
        another_filter = Filter('assignee = "Bob"')

        self._manager.append(mock_filter)
        self._manager.append(another_filter)
        self.assertEquals(1, len(self._manager))
        self.assertTrue(self._manager[0].hasobservers)
        self.assertEquals(1, len(self._manager[0]._observers))
        self.assertTrue(another_filter.observing)

    def test_append_appends_to_self_when_queries_differ(self):
        mock_filter = Filter('assignee = "Foo"')
        another_filter = Filter('assignee = "Bar"')

        self._manager.append(mock_filter)
        self._manager.append(another_filter)
        self.assertEquals(2, len(self._manager))
        self.assertFalse(another_filter.observing)

