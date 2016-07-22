"""
Contains resource items for mapping <project_manager> results
into ones recognised by the report
"""
from argparse import Action
from datetime import datetime, date, timedelta
from weeklyreport.log import Logger
from weeklyreport.decorators import accepts

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

class ResultList(list):
    """
    List of results returned by a <project manager>
    """
    _total = 0

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

    def __init__(self):
        """
        Create a new ResultList item
        """
        super().__init__()

    @accepts(Issue)
    def append(self, item):
        """
        Appends an Issue item to the list of results

        @param item Issue
        """
        super().append(item)


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
        for replacement in self:
            match = '{' + replacement.name.upper() + '}'
            if match in what:
                what = what.replace(match, str(replacement))
        return what

    @staticmethod
    @accepts(str)
    def release_date(value_format):
        """ helper function for getting the release date """
        # Releases are always on a Thursday
        today = date.today()
        releasedate = today + timedelta((3 - today.weekday()) % 7)

        return datetime.strftime(
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

    @staticmethod
    @accepts(str)
    def fix_version(value_format):
        """ Helper function for getting the fix version """
        today = date.today()
        releasedate = today + timedelta((3 - today.weekday()) % 7)

        return datetime.strftime(
            releasedate,
            value_format
        )

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
