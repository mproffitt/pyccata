import os
from unittest                   import TestCase
from mock                       import patch, PropertyMock
from ddt                        import ddt, data, unpack
from collections                import namedtuple
from weeklyreport.configuration import Configuration
from weeklyreport.resources import Replacements, ReplacementsValidator
from datetime import datetime, date, timedelta

@ddt
class TestReplacements(TestCase):
    _test_configuration_path = ''
    _required_root_elements = Configuration._required_root_elements


    @patch('weeklyreport.log.Logger.log')
    def setUp(self, mock_log):
        mock_log.return_value = None
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        self._mock_log = mock_log


    def tearDown(self):
        Configuration.NAMESPACE = 'weeklyreport'
        if Configuration._instance is not None:
            Configuration._instance = None
        if Configuration._configuration is not None:
            Configuration._configuration = None
        Configuration._required_root_elements = self._required_root_elements

        if Replacements._instance is not None:
            del Replacements._instance
            Replacements._instance = None

    @patch('weeklyreport.configuration.Configuration._parse_flags')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    @data(
        ['{SETUP}', 'a'],
        ['{NOSETESTS}', 'b'],
        ['{S}', 'c'],
        ['{COVERAGE}', 'd'],
        ['{BRANCHES}', 'e, x and z']
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

    @patch('weeklyreport.configuration.Configuration._parse_flags')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_replace_date_in_fix_version(self, mock_config_list, mock_arg):
        self.tearDown()
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='valid_config.json')
        config.check = True
        self.assertTrue(config.check)
        self.assertIsInstance(config.replacements, Replacements)

        today = date.today()
        releasedate = today + timedelta((3 - today.weekday()) % 7)

        value_format = '%Y-%m-%d'
        fixdate = datetime.strftime(
            releasedate,
            value_format
        )
        self.assertEquals(config.replacements.replace('{FIX_VERSION}'), fixdate)
        self.assertEquals(config.replacements.replace('some text'), 'Some Replacement Text')


    @patch('weeklyreport.configuration.Configuration._parse_flags')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_replace_date_in_release_date(self, mock_config_list, mock_arg):
        self.tearDown()
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='valid_config.json')
        config.check = True
        self.assertTrue(config.check)
        self.assertIsInstance(config.replacements, Replacements)

        today = date.today()
        releasedate = today + timedelta((3 - today.weekday()) % 7)

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

