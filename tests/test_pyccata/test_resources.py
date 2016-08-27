import os
import calendar
from unittest import TestCase
from mock import patch, PropertyMock
from ddt import ddt, data, unpack
from collections import namedtuple
from datetime import datetime, date, timedelta
import pandas as pd
from pyccata.core.configuration import Configuration


from pyccata.core.resources import Issue
from pyccata.core.resources import CommandLineResultItem
from pyccata.core.resources import ResultList
from pyccata.core.resources import Replacements
from pyccata.core.resources import ReplacementsValidator
from pyccata.core.resources import Calendar
from pyccata.core.log import Logger
from pyccata.bioinformatics.resources import BedFileItem

class TestIssueTypes(TestCase):

    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log):
        mock_log.return_value = None
        Logger._instance = mock_log

    def test_issue_keys_method(self):
        issue = Issue()
        self.assertEquals(20, len(issue.keys()))

    def test_bed_file_keys(self):
        bed_file = BedFileItem()
        self.assertEquals(20, len(bed_file.keys()))

    def test_command_line_result_keys(self):
        command_line = CommandLineResultItem()
        self.assertEquals(1, len(command_line.keys()))

    def test_update_from_dict(self):
        dictionary = {'line': 'hello world'}
        command_line = CommandLineResultItem()
        command_line.from_dict(dictionary)
        self.assertEquals('hello world', command_line.line)

    def test_to_series(self):
        issue = Issue()
        issue.key = 'ABC-123'
        issue.summary = 'Hello world'
        issue.issuetype = 'bug'

        self.assertIsInstance(issue.series, pd.Series)

class TestResultList(TestCase):
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log):
        mock_log.return_value = None
        Logger._instance = mock_log

    def test_result_list_from_pandas_dict(self):
        dictionary = {
            0: {'line': 'hello'},
            1: {'line': 'world'}
        }
        result_list = ResultList()
        result_list.dataframe = pd.DataFrame.from_dict(dictionary)
        self.assertIsInstance(result_list.dataframe, pd.DataFrame)

    def test_result_list_dataframe_returns_pandas_dict_if_called_directly(self):
        resultset = ResultList(name='test results')
        resultset.map_to(Issue())
        result_issue = Issue()
        result_issue.description = 'This is a test item'
        resultset.append(result_issue)

        another_result_issue = Issue()
        another_result_issue.description = 'This is a test item'
        resultset.append(another_result_issue)

        self.assertIsInstance(resultset.dataframe, pd.DataFrame)

@ddt
class TestReplacements(TestCase):
    _test_configuration_path = ''
    _required_root_elements = Configuration._required_root_elements


    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        mock_log.return_value = None
        mock_parser.return_value = []
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        Logger._instance = mock_log

    def tearDown(self):
        Configuration.NAMESPACE = 'pyccata.core'
        if Configuration._instance is not None:
            Configuration._instance = None
        if Configuration._configuration is not None:
            Configuration._configuration = None
        Configuration._required_root_elements = self._required_root_elements

        if Replacements._instance is not None:
            del Replacements._instance
            Replacements._instance = None

    @patch('pyccata.core.configuration.Configuration._parse_flags')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    @data(
        ['{SETUP}', 'a'],
        ['{NOSETESTS}', 'b'],
        ['{S}', 'c'],
        ['{COVERAGE}', 'd'],
        ['{BRANCHES}', 'e, x and z'],
        ['Look in your {HOME} directory', 'Look in your ' + os.environ.get('HOME') + ' directory'],
        ['HOME', os.environ.get('HOME')]
    )
    @unpack
    def test_replace_words_in_string(self, string, response, mock_config_list, mock_arg):
        self.tearDown()
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='valid_config.json')
        config.check = True
        self.assertTrue(config.check)
        self.assertIsInstance(config.replacements, Replacements)
        self.assertEquals(config.replacements.replace(string), response)

    @patch('pyccata.core.configuration.Configuration._parse_flags')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def test_replace_date_in_fix_version(self, mock_config_list, mock_arg):
        self.tearDown()
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='valid_config.json')
        config.check = True
        self.assertTrue(config.check)
        self.assertIsInstance(config.replacements, Replacements)
        config.replacements.find('FIX_VERSION').value = '28/Jul/2016'

        today = date.today()
        releasedate = today + timedelta((3 - today.weekday()) % 7)
        self.assertEquals(config.replacements.replace('{FIX_VERSION}'), '28/Jul/2016')
        self.assertEquals(config.replacements.replace('some text'), 'Some Replacement Text')


    @patch('pyccata.core.configuration.Configuration._parse_flags')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def test_replace_date_in_release_date(self, mock_config_list, mock_arg):
        self.tearDown()
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='valid_config.json')
        config.check = True
        self.assertTrue(config.check)
        self.assertIsInstance(config.replacements, Replacements)

        today = date.today()
        releasedate = Calendar().get_last_day_of_month_ahead()

        value_format = '%A, %d %B %Y'
        reldate = datetime.strftime(
            releasedate,
            value_format.replace('%d', '{th}')
        ).replace(
            '{th}',
            (str(releasedate.day) + (
                "th" if 4 <= releasedate.day % 100 <= 20 else {1:"st", 2:"nd", 3:"rd"}.get(
                    releasedate.day % 10, "th")
                )
            )
        )

        self.assertEquals(config.replacements.replace('{RELEASE_DATE}'), reldate)

    def test_replacements_validator_updates_replacements(self):
        self.tearDown()

        Config = namedtuple('Config', 'name type value overridable')
        config = Config(name='TEST', type='string', value='this is a test', overridable=False)
        class Namespace():
            test=None
            def __init__(self, test=None):
                self.test = test

        namespace = Namespace(test=None)

        replacements = Replacements(configuration=[config])
        replacement_validator = ReplacementsValidator(None, 'test')
        replacement_validator.__call__(None, namespace, 'hello world')

        self.assertEquals('hello world', replacements[0].value)

    def test_replacements_validator_does_not_update_lowercase_replacements(self):
        self.tearDown()

        Config = namedtuple('Config', 'name type value overridable')
        config = Config(name='test', type='string', value='this is a test', overridable=False)
        class Namespace():
            test=None
            def __init__(self, test=None):
                self.test = test

        namespace = Namespace(test=None)

        replacements = Replacements(configuration=[config])
        replacement_validator = ReplacementsValidator(None, 'test')
        replacement_validator.__call__(None, namespace, 'hello world')

        self.assertEquals('this is a test', replacements[0].value)

    def test_replacements_find_returns_none_if_replacement_is_not_cofigured(self):
        self.tearDown()

        Config = namedtuple('Config', 'name type value overridable')
        config = Config(name='test', type='string', value='this is a test', overridable=False)
        class Namespace():
            test=None
            def __init__(self, test=None):
                self.test = test

        namespace = Namespace(test=None)

        replacements = Replacements(configuration=[config])

        self.assertEquals(None, replacements.find('helloworld'))

class TestCalendar(TestCase):

    _calendar = None
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log):
        self._calendar = Calendar()
        mock_log.return_value = None
        Logger._instance = mock_log


    def test_get_month_and_year_14_months_from_now(self):
        date = datetime.today()
        year, month = self._calendar.get_month_and_year(14, date)
        self.assertEquals(date.year + 1, year)
        self.assertEquals(date.month + 2, month)

    def test_get_monday(self):
        for i in range(4):
            date = self._calendar.get_monday(i)
            self.assertEquals('Monday', datetime.strptime(str(date), '%Y-%m-%d').strftime('%A'))

    def test_today(self):
        today = datetime.today()
        compare = self._calendar.today()
        self.assertEquals(today.year, compare.year)
        self.assertEquals(today.month, compare.month)
        self.assertEquals(today.day, compare.day)

    def test_get_last_day_of_month_ahead_raises_attribute_error_if_day_is_invalid(self):
        with self.assertRaises(AttributeError):
            self._calendar.get_last_day_of_month_ahead('ImNotADay')

    @patch('pyccata.core.resources.Calendar.get_calendar_day')
    def test_for_five_week_month(self, mock_calendar):
        mock_calendar.side_effect = [IndexError('Five week month'), datetime.today()]
        cal = Calendar()
        date = cal.get_last_day_of_month_ahead()
        self.assertEquals(datetime.today().year, date.year)
        self.assertEquals(datetime.today().month, date.month)
        self.assertEquals(datetime.today().day, date.day)

    @patch('pyccata.core.resources.Calendar.get_last_day_of_month_ahead')
    @patch('pyccata.core.resources.Calendar.today')
    def test_get_release_day_skips_to_next_month_if_today_is_release_day(self, mock_calendar_today, mock_calendar):
        release_day = datetime.strptime('2016-07-28', '%Y-%m-%d')
        next_release = datetime.strptime('2016-08-31', '%Y-%m-%d')
        mock_calendar.side_effect = [release_day, next_release]

        mock_calendar_today.return_value = release_day
        self.assertEquals(next_release, self._calendar.get_release_day())
