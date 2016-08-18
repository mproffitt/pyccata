"""
Contains resource items for mapping <project_manager> results
into ones recognised by the report
"""
import os
import re
import sys
import calendar
import importlib
import inspect
from argparse import Action
from datetime import datetime
from releaseessentials.log import Logger
from releaseessentials.decorators import accepts
from releaseessentials.interface import ResultListInterface
from releaseessentials.exceptions import InvalidModuleError

class Attachment(object):
    """ Basic storage for a single attachment """

    #pylint: disable=too-few-public-methods
    # As a struct, no public methods are required.
    # Instead, all attributes are public

    def __init__(self):
        """ Store an attachment details as a struct """
        self.attachment_id = None
        self.filename = None
        self.mime_type = None



class Issue(object):
    """ Basic storage for a ticket item """

    #pylint: disable=too-many-instance-attributes
    # This object contains the relevant fields of a Jira ticket item
    # Therefore a large number of attributes are required.

    #pylint: disable=too-few-public-methods
    # As a struct, no public methods are required.
    # Instead, all attributes are public

    def __init__(self):
        """
        Initialise the Issue object as a struct
        """
        self.key = None
        self.summary = None
        self.issuetype = None
        self.created = None
        self.updated = None
        self.priority = None
        self.description = None
        self.status = None
        self.project = None
        self.fixversions = None
        self.resolution = None
        self.resolutiondate = None
        self.creator = None
        self.assignee = None
        self.release_text = None
        self.business_representative = None
        self.rollout_instructions = None
        self.rollback_instructions = None
        self.pipelines = None
        self.attachments = None

class ArgumentFlag():
    """
       Wrapper class for command line arguments defined in config
    """
    #pylint: disable=too-few-public-methods
    # As a struct, no public methods are required.
    # Instead, all attributes are public

    shortname = ''
    longname = ''
    description = ''
    default = None
    action = None

    def __init__(self, shortname=None, longname=None, description=None, default=None, action=None):
        """
        Initiate the structure
        """
        #pylint: disable=too-many-arguments
        self.shortname = shortname
        self.longname = longname
        self.description = description
        self.default = default
        self.action = action

class Calendar:
    """
    Provides specific calendar information required by the release process
    """
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    def get_month_and_year(self, month_ahead, date_from):
        """
        Gets the year and month one year from now
        """
        # pylint: disable=no-self-use
        # This is intended to be referenced by self rather than Calendar
        year = date_from.year
        month = date_from.month
        if month + month_ahead <= 12:
            month = month + month_ahead
        else:
            month = (month + month_ahead) - 12
            year += 1
        return (year, month)


    def get_calendar_day(self, day_number, week_number, month_ahead=0, date_from=datetime.now()):
        """
        Gets the date of a day n months in the future

        @param day_number  int
        @param week_number int
        @param month_ahead int
        @param date_from   datetime

        @return datetime
        """
        year, month = self.get_month_and_year(month_ahead, date_from)
        return calendar.Calendar(week_number).monthdatescalendar(year, month)[day_number][0]

    def get_monday(self, week_number, month_ahead=0, date_from=datetime.now()):
        """
        Gets the date of the Monday of a given week in a given month
        """
        year, month = self.get_month_and_year(month_ahead, date_from)
        return calendar.Calendar().monthdatescalendar(year, month)[week_number][Calendar.MONDAY]

    def today(self):
        """
        Gets today (wrapper for datetime.today for test purposes)
        """
        # pylint: disable=no-self-use
        # This is intended to be referenced by self rather than Calendar
        return datetime.today()

    def get_last_day_of_month_ahead(self, day_name='wednesday', month_from_now=0):
        """
        Gets the last occurance of a day in a given month

        @param day_name string

        @return datetime.date

        @throw InvalidArgumentError if day_name is not a valid day (Monday - Sunday)
        """
        day_number = getattr(Calendar, day_name.upper()) if hasattr(Calendar, day_name.upper()) else False
        if not day_number:
            raise AttributeError('Day provided (' + day_name + ') is not valid')

        try:
            # five week month
            current_date = self.get_calendar_day(5, day_number, month_from_now)
        except IndexError:
            # Normal month
            current_date = self.get_calendar_day(4, day_number, month_from_now)
        return current_date

    def get_release_day(self, release_on='Wednesday'):
        """
        Gets the day a monthly release will fall on as a day within the last week of the month.

        @param release_on string [Monday - Sunday]

        @return datetime.date
        """
        current_date = self.get_last_day_of_month_ahead(release_on, month_from_now=0)
        if self.today().day >= current_date.day:
            current_date = self.get_last_day_of_month_ahead(release_on, month_from_now=1)
        return current_date


class ResultList(list):
    """
    List of results returned by a <project manager>
    """
    __implements__ = (ResultListInterface,)
    _namespace = None
    _total = 0
    _collate = None
    _distinct = False
    _field = False

    def __init__(self, collate=None, distinct=False, namespace=None):
        """
        Create a new ResultList item
        """
        self._namespace = namespace
        self.collate = collate
        self.distinct = distinct
        super().__init__()

    @property
    def field(self):
        """ Gets the field used for collation """
        return str(self._field)

    @property
    def collate(self):
        """
        Get the collation of this result set

        @return string
        """
        if self._collate is None:
            return self
        return self._collate(self)

    @collate.setter
    def collate(self, collation):
        """
        Set the collation method of this ResultList
        """
        function = None
        if isinstance(collation, tuple):
            self._field = collation.field
            collation = collation.method

        try:
            function = self._import(collation)
        except InvalidModuleError as exception:
            if collation is not None:
                Logger().error('Failed to set collation method')
                Logger().error(exception)
        self._collate = function

    @property
    def distinct(self):
        """ Is this result set distinct """
        return self._distinct

    @distinct.setter
    @accepts(bool)
    def distinct(self, distinct):
        """
        Set whether this resultset should be filled with distinct values

        This is only used in collation of results.
        """
        self._distinct = distinct

    @property
    def total(self):
        """
        Get the total number of items returned by the query
        """
        return self._total

    @total.setter
    @accepts(int)
    def total(self, value):
        """
        Set the total value

        @param total int
        """
        self._total = value

    @accepts(Issue)
    def append(self, item):
        """
        Appends an Issue item to the list of results

        @param item Issue
        """
        super().append(item)

    @accepts(list)
    def extend(self, results):
        """
        Extends the current list of results with the set given

        @param result ResultList
        """
        for item in results:
            self.append(item)

    def _import(self, name):
        """
        Attempts to import the collation method from the collation module
        """
        module_name = str(self._namespace) + '.' + 'collation'
        try:
            importlib.import_module(module_name)
            functions = inspect.getmembers(sys.modules[module_name], inspect.isfunction)
            return [function for function in functions if function[0].lower() == name.lower()][0][1]
        except (IndexError, AttributeError, ImportError):
            raise InvalidModuleError(str(name), str(module_name))

class ReplacementsValidator(Action):
    """
    Sets the value of replacement string from a command line flag

    When adding command line arguments for text replacements,
    this class is added automatically as an action to update
    the value of replacements defined within the JSON structure.
    """
    #pylint: disable=too-few-public-methods
    # This is a struct class and therefore
    # has no public methods.

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Wrapper for validation of command line arguments passed to
        the replacements class
        """
        replacements = Replacements()
        for key, replacement in enumerate(replacements):
            if replacement.name == self.dest.upper():
                replacements[key].value = values

        setattr(namespace, self.dest, values)

class Replacement(object):
    """
    Keys and their respective replacement
    """
    #pylint: disable=too-few-public-methods
    # This is a struct class and therefore
    # has no public methods.
    name = None
    value = None
    _function = None

    def __init__(self, name='', value='', function=None):
        self.name = name
        self.value = value
        self._function = function

    def __str__(self):
        """ Gets the value as a string using the callback function as necessary """
        return self._function(self.value) if self._function is not None else self.value

class Replacements(list):
    """
    List of replacements for the current document

    This list is compiled from the configuration file by
    parsing the "replacements" field.
    """
    _instance = None
    _configuration = []
    _flags = []
    _is_loaded = None

    @accepts(configuration=(None, list, tuple))
    def __init__(self, configuration=None):
        """
        Create a new list of replacements
        """
        if configuration is None:
            configuration = []

        if self._is_loaded:
            return
        self._configuration = configuration

        super().__init__()
        self.setup()

    def setup(self):
        """
        Initialises the list of replacements
        """
        for replacement in self._configuration:
            self.append(
                self._get_replacement(replacement)
            )
        self._is_loaded = True

    def _get_replacement(self, replacement):
        """
        Parses a string replacement
        """
        name = getattr(replacement, 'name')
        function_name = getattr(replacement, 'type')
        function = None
        if hasattr(Replacements, function_name):
            function = getattr(Replacements, function_name)
        value = getattr(replacement, 'value')
        overridable = getattr(replacement, 'overridable')
        if overridable is not False:
            self._flags.append(
                ArgumentFlag(
                    shortname=getattr(replacement.overridable, 'abbrev'),
                    longname=getattr(replacement.overridable, 'flag'),
                    description=(
                        getattr(replacement.overridable, 'help') if hasattr(replacement.overridable, 'help') else ''
                    ),
                    default=value,
                    action=ReplacementsValidator
                )
            )

        return Replacement(
            name=name,
            value=value,
            function=function
        )

    @accepts(str)
    def replace(self, what):
        """
        Swaps out keyword matching {WHAT} in a string of text for a given value
        """
        # replace newlines
        newlines = re.compile(r'(\r\n|\r|\n)+')
        what = newlines.sub('\n', what)

        # replace from config
        for replacement in self:
            match = '{' + replacement.name.upper() + '}'
            if match in what:
                what = what.replace(match, str(replacement))
            elif replacement.name.upper() == what.upper():
                what = str(replacement)

        # replace from environement
        for replacement in os.environ:
            match = '{' + replacement.upper() + '}'
            if match in what:
                what = what.replace(match, str(os.environ.get(replacement)))
            elif replacement.upper() == what.upper():
                what = str(os.environ.get(replacement))


        return what

    def find(self, what):
        """
        Finds an item in the Replacements list by name

        @param what string

        @return Replacement if what matches name else None
        """
        for item in self:
            if item.name == what:
                return item
        return None

    @staticmethod
    @accepts(str)
    def release_date(value_format):
        """ helper function for getting the release date """
        replacements = Replacements()

        release_date = datetime.strptime(
            replacements.replace('{FIX_VERSION}'),
            replacements.find('FIX_VERSION').value
        )

        return datetime.strftime(
            release_date,
            value_format.replace('%d', '{th}')
        ).replace(
            '{th}',
            (str(release_date.day) + (
                "th" if 4 <= release_date.day % 100 <= 20 else {1:"st", 2:"nd", 3:"rd"}.get(
                    release_date.day % 10, "th")
                )
            )
        )

    @staticmethod
    @accepts(str)
    def fix_version(value_format):
        """ Helper function for getting the fix version """
        release_day = Replacements().replace('{RELEASE_DAY}')
        release_date = Calendar().get_release_day(release_day)
        return datetime.strftime(release_date, value_format)

    @staticmethod
    @accepts(str)
    def csv(value):
        """ if value is a csv formatted string, split it, add spaces and add an 'and' """
        return ' and'.join(
            ', '.join(value.split(',')).rsplit(',', 1)
        )

    @property
    def flags(self):
        """ Gets a list of flags defined by the configuration """
        return self._flags

    def __new__(cls, configuration=None):
        """
        Override for __new__ to check if Replacements has already been loaded.
        """
        #pylint: disable=unused-argument
        # Arguments passed to this method are for the construcor and
        # handled by python in passing to __init__
        if cls._instance is None:
            Logger().debug('Loading singleton replacements')
            cls._is_loaded = False
            cls._instance = super(Replacements, cls).__new__(cls)
        return cls._instance
