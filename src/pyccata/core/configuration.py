"""
Configuration module
"""
import os
import json
from collections import namedtuple
from argparse import ArgumentParser

import matplotlib

from pyccata.core.log import Logger
from pyccata.core.decorators import accepts
from pyccata.core.helpers import class_exists
from pyccata.core.exceptions import RequiredKeyError
from pyccata.core.exceptions import InvalidClassError
from pyccata.core.resources import Replacements

matplotlib.use("Cairo")

class Configuration(object):
    """
        Configuration is loaded from JSON format and parsed into
        a named tuple stored within this class.

        Access is via direct wrappers which parse and validate
        using the static {{validate}} method.

    """
    # pylint: disable=too-many-instance-attributes
    CONFIG_DIRECTORY_NAME = 'pyccata'
    NAMESPACE = 'pyccata.core'
    REPORTING_TYPES = [
        'pdf', 'docx', 'html', 'latex', 'null'
    ]
    IMAGE_INDEX = 0

    _is_loaded = False
    _instance = None
    _configuration = None
    _manager = None
    _reporting = None
    _replacements = None
    _parser = None

    _required_root_elements = [
        'manager',
        'reporting'
    ]

    @staticmethod
    def _xdg_config_home():
        """ Check to see if os Environment variable XDG_CONFIG_HOME is defined or return empty string """
        return os.environ.get('XDG_CONFIG_HOME') if os.environ.get('XDG_CONFIG_HOME') is not None else ''

    @property
    def locations(self):
        """ public synonym for Configuration._get_locations """
        return self._get_locations()

    @property
    def manager(self):
        """ Get the configured manager """
        return self._manager

    @manager.setter
    def manager(self, manager):
        """
        Verify the manager class exists and set its name if true

        @raise RequiredKeyError  if a root element of the same name as manager is not defined.
        @raise InvalidClassError if the required class does not exist under NAMESPACE.module

        Example configuration:
            {
                "manager": "jira",
                "jira": " {
                    ...
                }
            }

        Example module structure:
            pyccata.core
            |-- managers
                |-- clients
                    |-- jira.py
                        class Jira(ManagerInterface):
                            ___implements__ = (ManagerInterface,)
        """
        Logger().info('Loading manager class \'{0}\''.format(manager))
        if not hasattr(self._configuration, manager):
            raise RequiredKeyError('\'<root>/{0}'.format(manager))

        class_path = '{0}.managers.clients.{1}'.format(self.NAMESPACE, manager.lower())
        if not class_exists(self.NAMESPACE, 'managers.clients', manager.title()):
            raise InvalidClassError(manager, class_path)
        self._manager = manager

    @property
    def reporting(self):
        """ Get the configured reporting interface """
        return self._reporting

    @reporting.setter
    def reporting(self, reporting):
        """
        Verify the reporting class exists and set its name if true

        @raise RequiredKeyError  if a root element of the same name as manager is not defined.
        @raise InvalidClassError if the required class does not exist under NAMESPACE.module

        Example configuration:
            {
                "reporting": "docx",
                "report": " {
                    ...
                }
            }

        Example module structure:
            pyccata.core
            |-- managers
                |-- clients
                    |-- docx.py
                        class Docx(ReportingInterface):
                            ___implements__ = (ReportingInterface,)
        """
        Logger().info('Loading reporting class \'{0}\''.format(reporting))
        if not hasattr(self._configuration, 'report'):
            raise RequiredKeyError('\'<root>/report')

        class_path = '{0}.clients.{1}'.format(self.NAMESPACE, reporting)
        if not class_exists(self.NAMESPACE, 'managers.clients', reporting):
            raise InvalidClassError(reporting, class_path)
        self._reporting = reporting

    @property
    def replacements(self):
        """
        Handles all replacements provided in the configuration
        """
        return self._replacements


    def __init__(self, filename='configuration.json', dont_parse=False):
        """
        Initialise the Configuration

        :param string: filename The name of the file to load
        :param bool:   dont_parse [optional] default False

        If dont_parse is set, the Configuration object will skip parsing command line arguments.
        This is useful when loading the object inside a Jupyter notebook.
        """
        if self._is_loaded:
            return
        self._filename = filename
        self._dont_parse = dont_parse
        self._load()

    def __getattr__(self, name):
        """
        Get an attribute from the JSON

        When calling configuration attributes, if the attribute
        can't be found, look for it in the JSON object
        """
        if hasattr(self._configuration, name):
            return getattr(self._configuration, name)
        raise AttributeError('Configuration object has no attribute \'{0}\''.format(name))

    def _load(self):
        """
        Attempts to load the configuration file from JSON
        """
        for location in self._get_locations():
            Logger().debug('Checking for config file in \'{0}\''.format(location))
            path = os.path.join(str(location), self._filename)
            try:
                with open(path) as configuration_file:
                    self._configuration = json.load(
                        configuration_file,
                        object_hook=lambda x: namedtuple('Config', x.keys())(*x.values())
                    )
                    Logger().debug('Using configuration from \'{0}\'.'.format(path))
                    break
            except IOError:
                pass
        if not self._configuration:
            raise IOError('Invalid configuration file or path not provided (got \'{0}\')'.format(self._filename))
        self.validate_config(self._required_root_elements)
        if hasattr(self._configuration, 'replacements'):
            self._replacements = Replacements(configuration=self._configuration.replacements)
        if not self._dont_parse:
            self._parse_flags()
        self._is_loaded = True

    def _get_locations(self):
        """
        Returns a list of locations which might contain the configuration file

        @return list
        """
        return [
            os.getcwd(),
            os.path.join(Configuration._xdg_config_home(), self.CONFIG_DIRECTORY_NAME),
            os.path.join(os.path.expanduser('~'), '.{0}'.format(self.CONFIG_DIRECTORY_NAME)),
            '/etc/{0}'.format(self.CONFIG_DIRECTORY_NAME),
            os.environ.get('REPORT_CONFIG_PATH'),
            os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf')
        ]

    @accepts(list)
    def validate_config(self, required_elements=list):
        """
        Test to see if the configuration is valid against the object infrastructure

        @return bool
        """
        for element in required_elements:
            if not hasattr(self._configuration, element):
                raise RequiredKeyError('<root>/{0}'.format(element))
            setattr(self, element, getattr(self._configuration, element))
        return True

    def _parse_flags(self):
        """
        Parses flags provided on the command line and adds them to the current configuration
        """
        self._setup_parser()

        #pylint: disable=protected-access
        for key in self._configuration._fields:
            item = getattr(self, key) if hasattr(self, key) else getattr(self._configuration, key)
            if hasattr(item, 'flags'):
                for flag in item.flags:
                    if flag.shortname == '':
                        self._parser.add_argument(
                            flag.longname,
                            help=flag.description,
                            default=flag.default,
                            action=flag.action
                        )
                    else:
                        self._parser.add_argument(
                            flag.shortname,
                            flag.longname,
                            help=flag.description,
                            default=flag.default,
                            action=flag.action
                        )
        self._parse_args()

    def _setup_parser(self):
        """
        Gets a new argparse.ArgumentParser object
        """
        self._parser = ArgumentParser()

    def _parse_args(self):
        """
        Parse command line options
        """
        self._parser.parse_args()


    def __new__(cls, filename='configuration.json', dont_parse=False):
        """
        Override for __new__ to check if Configuration has already been loaded.
        """
        # pylint: disable=unused-argument
        # dont_parse is passed straight through to the init call.
        # We don't need it in this method
        if cls._instance is None:
            Logger().debug('Loading singleton configuration with filename {0}'.format(filename))
            cls._is_loaded = False
            cls._instance = super(Configuration, cls).__new__(cls)
        return cls._instance
