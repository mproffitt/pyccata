"""
Contains resource items for mapping <project_manager> results
into ones recognised by the report
"""

# pylint: disable=too-many-lines
# This module should be broken down into multiple
# resource files but for now it stays as is.

import os
import re
import sys
import calendar
import importlib
import inspect
import copy
import subprocess
from argparse import Action
from datetime import datetime
import pandas as pd
from pyccata.core.helpers import collation
from pyccata.core.log import Logger
from pyccata.core.decorators import accepts
from pyccata.core.interface import ResultListInterface
from pyccata.core.interface import ResultListItemInterface
from pyccata.core.exceptions import InvalidArgumentNumberError
from pyccata.core.exceptions import InvalidModuleError
from pyccata.core.helpers import implements

class ResultListItemAbstract(object):
    """
    Abstract base class for ResultListItems
    """
    # pylint: disable=too-few-public-methods
    # As a struct, no public methods are required.
    # Instead, all attributes are public

    __implements__ = (ResultListItemInterface,)

    @accepts(dict)
    def from_dict(self, dictionary):
        """
        Reloads the object dictionary from another
        """
        self.__dict__.update(dictionary)
        return self

    @property
    def series(self):
        """
        Convert a dictionary to a pandas series
        """
        return pd.Series(self.__dict__)

class Issue(ResultListItemAbstract):
    """ Basic storage for a ticket item """

    # pylint: disable=too-many-instance-attributes
    # This object contains the relevant fields of a Jira ticket item
    # Therefore a large number of attributes are required.

    # pylint: disable=too-few-public-methods
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

    def keys(self):
        """ Gets the list of issue keys """
        return list(self.__dict__.keys())

class Join(object):
    """
    Provides instructions on how to join datasets
    """
    _method = None
    _column = None

    @accepts(str, (str, list))
    def __init__(self, method, column):
        self._method = method
        self._column = column

    @property
    def method(self):
        return self._method

    @property
    def column(self):
        return self._column

class Collation(object):
    """
    The collation object provides functionality for filtering
    data inside collation methods utilised by datasets extending
    the ResultList class
    """
    _method = None
    _field = None
    _columns = None
    _query = None
    _group_by = None
    _join = None
    _limits = None
    _split_results = False

    @accepts(
        str,
        field=(str, list),
        columns=(list, None),
        query=(str, object),
        group_by=(str, list),
        join=(None, Join),
        split_results=bool,
        limits=(object, None),
        namespace=str
    )
    def __init__(
            self,
            method,
            field='',
            columns=None,
            query='',
            group_by='',
            join=None,
            split_results=False,
            limits=None,
            namespace=''
    ):
        self._namespace = namespace
        self._field = field
        self._query = query
        self._group_by = group_by
        self._columns = columns
        self._join = join
        self._limits = limits
        self.method = method

    def __call__(self, results):
        try:
            return self._method(results, self)
        except (InvalidArgumentNumberError, AttributeError):
            return self._method(results)

    @property
    def method(self):
        return self._method

    @method.setter
    @accepts(str)
    def method(self, collation):
        try:
            function = self._import(collation)
        except InvalidModuleError as exception:
            if collation is not None:
                Logger().error('Failed to set collation method')
                Logger().error(exception)
                raise exception
        self._method = function

    @property
    def columns(self):
        return self._columns

    @property
    def field(self):
        return self._field

    @property
    def query(self):
        return self._query

    @property
    def group_by(self):
        return self._group_by

    @property
    def join(self):
        return self._join

    @property
    def limits(self):
        return self._limits

    @property
    def split_results(self):
        return self._split_results

    def _import(self, name):
        """
        Attempts to import the collation method from the collation module
        module_name = str(self._namespace) + '.collation'
        try:
            importlib.import_module(module_name)
            functions = inspect.getmembers(sys.modules[module_name], inspect.isfunction)
            return [function for function in functions if function[0].lower() == name.lower()][0][1]
        except (IndexError, AttributeError, ImportError):
            raise InvalidModuleError(str(name), str(module_name))
        """
        return collation(name, self._namespace)

    @staticmethod
    def get(collation, namespace):
        if isinstance(collation, str):
            return Collation(collation, namespace=namespace)

        join = None
        if hasattr(collation, 'join'):
            method = collation.join.method if hasattr(collation.join, 'method') else None
            column = collation.join.column if hasattr(collation.join, 'column') else None
            if method is not None:
                join = Join(method, column)

        return Collation(
            collation.method,
            field=collation.field if hasattr(collation, 'field') else '',
            columns=collation.columns if hasattr(collation, 'columns') else None,
            query=collation.query if hasattr(collation, 'query') else '',
            group_by=collation.group_by if hasattr(collation, 'group_by') else '',
            join=join,
            split_results=collation.split_results if hasattr(collation, 'split_results') else False,
            limits=collation.limits if hasattr(collation, 'limits') else None,
            namespace=namespace
        )

class CommandLineResultItem(ResultListItemAbstract):
    """ Basic storage for a command line result item """
    # pylint: disable=too-few-public-methods
    # As a struct, no public methods are required.
    # Instead, all attributes are public

    def __init__(self):
        """
        Create a new CommandLineResultItem
        """
        self.line = None

    def keys(self):
        """
        Gets the object keys
        """
        return list(self.__dict__.keys())

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
    # pylint: disable=too-many-instance-attributes
    # This object contains the relevant fields of a Jira ticket item
    # Therefore a large number of attributes are required.

    __implements__ = (ResultListInterface, ResultListItemInterface)
    _namespace = None
    _name = None
    _total = 0
    _collate = None
    _distinct = False
    _field = None
    _dataframe = None
    _mapping_item = None
    _columns = None
    _group_by = None
    _subquery = None

    def __init__(self, name=None, collate=None, distinct=False, namespace=None):
        """
        Create a new ResultList item
        """
        self._namespace = namespace
        self._name = name
        self.collate = collate
        self.distinct = distinct
        super().__init__()

    # =============================================
    # Magic methods for creating iterable object
    #

    def __getitem__(self, key):
        if self.dataframe is not None:
            return self._get_item(dict(self.dataframe.iloc[key]))
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if self._dataframe is not None:
            self._dataframe.at[key] = value.series() if isinstance(value, ResultListInterface) else pd.Series(value)
        super().__setitem__(key, value)

    def __len__(self):
        if self._dataframe is not None:
            return len(self._dataframe.index)
        return super().__len__()

    def __delitem__(self, key):
        if self._dataframe is not None:
            return self._dataframe.__delitem__(key)
        return super().__delitem__(key)

    def __iter__(self):
        if self._dataframe is not None:
            return self._dataframe.itertuples()
        return super().__iter__()

    def __reversed__(self):
        if self._dataframe is not None:
            return self._dataframe.reindex(index=self._dataframe.index[::-1])
        return super().__reversed__()

    def type(self):
        """
        Gets the type of item stored in this object
        """
        return type(self._mapping_item)

    @property
    def name(self):
        """
        Get the name assigned to this set
        """
        return self._name if self._name is not None else ''

    @property
    def group_by(self):
        """ Group the results """
        return self._group_by

    @group_by.setter
    def group_by(self, group_by):
        """ Group the results on a particular column (also used for joins) """
        self._group_by = group_by

    @property
    def columns(self):
        """ Gets the column headings """
        if self._dataframe is not None:
            return self._dataframe.columns
        else:
            return self._columns

    @property
    def field(self):
        """ Gets the field used for collation """
        return str(self._collate.field) if self._field is None and self._collate is not None else str(self._field)

    @property
    def collation(self):
        """
        Get the collation method defined for this ResultList
        """
        return self._collate

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
    @accepts((None, Collation))
    def collate(self, collation):
        """
        Set the collation method of this ResultList
        """
        self._collate = collation

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

    def from_dict(self, dictionary):
        """
        Converts a dictionary into the type stored in _mapping_item
        """
        if isinstance(dictionary, dict) and self._mapping_item is not None:
            item = copy.deepcopy(self._mapping_item)
            item.__init__()
            return item.from_dict(dictionary)
        return dictionary

    @accepts(ResultListItemInterface)
    def map_to(self, what):
        """
        The map_to method allows setting of a specific type to map a pandas dataframe against.

        @param what ResultListItemInterface

        When loading from the dataframe instead of directly, a mapping item
        must be set on the ResultList. This can either be achieved by assgning
        the dataframe with a tuple such that: `ResultList::dataframe = (dataframe, ResultListItemInterface)`
        or by calling `map_to` prior to assigning the dataframe:

        @example
            results = ResultList()
            results.map_to(Issue())
            results.dataframe = pandas.DataFrame(...)
        """
        self._mapping_item = what

    @property
    def dataframe(self):
        """
        Get the dataframe for this object, creating as necessary
        """
        if self._dataframe is not None:
            return self._dataframe
        if len(self) > 0 and self._mapping_item is not None:
            variables = []
            dataframe_rows = []
            for item in self:
                row = []
                new_item = self.from_dict(item)
                for field in self._mapping_item.keys():
                    if hasattr(new_item, field) and getattr(new_item, field) is not None:
                        if field not in variables:
                            variables.append(field)
                        row.append(getattr(new_item, field))
                if len(row) > 0:
                    dataframe_rows.append(row)
                del row

            self._dataframe = pd.DataFrame(dataframe_rows, columns=variables)
        return self._dataframe

    @dataframe.setter
    @accepts((tuple, pd.DataFrame))
    def dataframe(self, dataframe):
        """
        Sets the dataframe from a Pandas search
        """
        if not isinstance(dataframe, tuple):
            self._dataframe = dataframe
        else:
            self._dataframe, self._mapping_item = dataframe

    @accepts(ResultListItemInterface)
    def append(self, item):
        """
        Appends an Issue item to the list of results

        @param item Issue
        """
        try:
            if self.columns is None:
                check = item[0]
                if isinstance(item[0], ResultList):
                    check = check[0]
                if check is not None:
                    self._columns = [
                        key for key in check.keys() if hasattr(check, key) and getattr(check, key) is not None
                    ]
        except TypeError:
            pass

        if isinstance(item, pd.Series):
            self.dataframe.append(item)
        else:
            super().append(item)

    @accepts(list)
    def extend(self, results):
        """
        Extends the current list of results with the set given

        @param result ResultList

        """
        for item in results:
            self.append(item if implements(item, ResultListItemInterface) else self._get_item(item))

    def copy(self):
        """
        Returns deep copy of the current result set

        copy.deepcopy cannot be used directly on the ResultSet
        due to issues with copying the dataframe and loading back.
        Use this method to generate a deepcopy of the set instead
        """
        return_item = type(self)()
        return_item[:] = list(self[:])
        return_item._namespace = copy.deepcopy(self._namespace)
        return_item._name = copy.deepcopy(self._namespace)
        return_item._total = copy.deepcopy(self._total)
        return_item._collate = copy.deepcopy(self._collate)
        return_item._distinct = copy.deepcopy(self._distinct)
        return_item._field = copy.deepcopy(self._field)
        return_item._dataframe = copy.deepcopy(self._dataframe)
        return_item._mapping_item = copy.deepcopy(self._mapping_item)
        return_item._columns = copy.deepcopy(self._columns)
        return_item._group_by = copy.deepcopy(self._group_by)
        return return_item

    def _get_item(self, dictionary):
        """
        Converts a dictionary to a copy of the mapping item

        @param dictionary dict
        """
        item = None
        if dictionary is not None and self._mapping_item is not None:
            item = copy.deepcopy(self._mapping_item)
            item.from_dict(dictionary)
        return item

class MultiResultList(ResultList):
    """
    Holder for the contents of multiple result sets
    """
    __implements__ = (ResultListItemInterface,)

    _combine = False
    _group_by = None

    @accepts(ResultList)
    def append(self, item):
        """ Add a result list item to the list of results """
        super().append(item)

    @property
    def combine(self):
        """
        If true, will cause the results to be merged to a single set

        Default False
        """
        return self._combine

    @combine.setter
    @accepts(bool)
    def combine(self, combine):
        """
        Set to True to have the result sets combined to a single set

        @param combine bool
        """
        self._combine = combine

    @property
    def distinct(self):
        return self._distinct

    @distinct.setter
    def distinct(self, distinct):
        self._distinct = distinct
        for result in self:
            result.distinct = distinct

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

    @accepts(str, additional=(None, dict))
    def replace(self, what, additional=None):
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

        # replace additional
        if additional is not None:
            for replacement in additional:
                match = '{' + replacement + '}'
                if match in what:
                    what = what.replace(match, str(additional[replacement]))
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

class Command(object):
    """
    Private struct describing a command

    This class should not be implemented directly. Use ThreadableCommand
    """
    def __init__(self):
        self.command = None
        self.arguments = []
        self.redirects = []
        self.return_code = -1

        self._stdout = None
        self._stderr = None

    @property
    def stdout(self):
        """
        Get standard output location
        """
        for redirect in self.redirects:
            if isinstance(redirect.redirect_input, list):
                self._stdout = self._get_redirect(Redirect.STDOUT, redirect.redirect_output)
                self._stderr = self._stdout
            elif redirect.redirect_input == Redirect.STDOUT:
                self._stdout = self._get_redirect(Redirect.STDOUT, redirect.redirect_output)
        return self._stdout if self._stdout is not None else subprocess.PIPE

    @property
    def stderr(self):
        """
        Get the standard error location
        """
        for redirect in self.redirects:
            if isinstance(redirect.redirect_input, list):
                self._stderr = self._get_redirect(Redirect.STDERR, redirect.redirect_output)
                self._stdout = self._stderr
            elif redirect.redirect_input == Redirect.STDERR:
                self._stderr = self._get_redirect(Redirect.STDERR, redirect.redirect_output)
        return self._stderr if self._stderr is not None else subprocess.PIPE

    def _get_redirect(self, redirect_input, redirect_output):
        """
        Gets where the redirect is to be sent to (STDOUT | SDTERR | file)

        @param redirect_input  int What is being redirected
        @param redirect_output int Where to redirect to

        @return mixed

        This method will return None if no redirect can be found, subprocess.STDOUT if
        stderr is being redirected to stdout or a file handle if a file is requested.
        """
        if redirect_input == Redirect.STDOUT:
            if isinstance(redirect_output, int) and redirect_output == Redirect.STDERR:
                return self.stderr
            return Command._get_file_handle(redirect_output)

        if isinstance(redirect_output, int) and redirect_output == Redirect.STDOUT:
            return subprocess.STDOUT
        return Command._get_file_handle(redirect_output)

    @staticmethod
    def _get_file_handle(filename):
        """
        Return a file handle opened in append mode

        @param filename string
        @return Filehandle opened by `open`
        """
        return open(filename, mode='a')

class Redirect(object):
    """
    Handles Redirects for commands

    This class should not be implemented directly. Use ThreadableCommand instead
    """
    # pylint: disable=too-few-public-methods
    # This class is effectively a private struct for the Command class
    STDOUT = 1
    STDERR = 2
    _redirects = [STDOUT, STDERR]

    redirect_input = None
    redirect_output = None

    def __init__(self, redirect_input=None, redirect_output=None):
        """
        Create a new redirect
        """
        if isinstance(redirect_input, int):
            try:
                # the left side of a redirect (>) may be &
                self.redirect_input = self._redirects[(int(redirect_input) - 1)]
            except IndexError:
                pass
        if redirect_input == '&':
            self.redirect_input = [
                self._redirects[0],
                self._redirects[1]
            ]

        self.redirect_output = redirect_output
        try:
            self.redirect_output = int(self.redirect_output)
        except ValueError:
            pass

        if isinstance(redirect_output, int):
            try:
                self.redirect_output = self._redirects[int(redirect_output) - 1]
            except IndexError:
                pass

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
