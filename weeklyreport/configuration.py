"""
Configuration module
"""
import os
import json
from collections             import namedtuple
from weeklyreport.log        import Logger
from weeklyreport.decorators import accepts
from weeklyreport.helpers    import class_exists
from weeklyreport.exceptions import RequiredKeyError, InvalidClassError
class Configuration(object):
    """
        Configuration is loaded from JSON format and parsed into
        a named tuple stored within this class.

        Access is via direct wrappers which parse and validate
        using the static {{validate}} method.

    """
    CONFIG_DIRECTORY_NAME = 'releaseessentials'
    NAMESPACE = 'weeklyreport'
    _instance = None
    _configuration = None
    _manager = None

    _required_root_elements = [
        'manager'
    ]

    @staticmethod
    def _xdg_config_home():
        """ Check to see if os Environment variable XDG_CONFIG_HOME is defined or return empty string """
        return os.environ.get('XDG_CONFIG_HOME') if os.environ.get('XDG_CONFIG_HOME') is not None else ''

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
            weeklyreport
            |-- managers
                |-- jira.py
                    class Jira(ManagerInterface):
                        ___implements__ = (ManagerInterface,)
        """
        Logger().info('Loading manager class \'{0}\''.format(manager))
        if not hasattr(self._configuration, manager):
            raise RequiredKeyError('\'<root>/{0}'.format(manager))

        class_path = '{0}.managers.{1}'.format(self.NAMESPACE, manager)
        if not class_exists(self.NAMESPACE, 'managers', manager):
            raise InvalidClassError(manager, class_path)
        self._manager = manager


    def __init__(self, filename='configuration.json'):
        """ Initialise the Configuration """
        self._filename = filename
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
                    if self._configuration is not None:
                        Logger().debug('Using configuration from \'{0}\'.'.format(path))
                        break
            except IOError:
                pass
        if not self._configuration:
            raise IOError('Invalid configuration file or path not provided (got \'{0}\''.format(self._filename))
        self.validate_config(self._required_root_elements)

    def _get_locations(self):
        """
        Returns a list of locations which might contain the configuration file

        @return list
        """
        return [
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
                Logger().debug('checking for \'<root>/{0}\''.format(element))
                raise RequiredKeyError('<root>/{0}'.format(element))
            if hasattr(self, element):
                setattr(self, element, getattr(self._configuration, element))
        return True

    def __new__(cls, filename='configuration.json'):
        """
        Override for __new__ to check if config has already been loaded.
        """
        if cls._instance is None:
            Logger().debug('Loading singleton configuration with filename {0}'.format(filename))
            cls._instance = super(Configuration, cls).__new__(cls)
        return Configuration._instance
