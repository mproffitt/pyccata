"""
Manager base class
"""
import importlib
from pyccata.core.decorators import accepts
from pyccata.core.exceptions import InvalidModuleError
from pyccata.core.exceptions import InvalidClassError
from pyccata.core.helpers import implements
from pyccata.core.configuration import Configuration
from pyccata.core.exceptions import RequiredKeyError

class Manager(object):
    """
    Abstract base class for manager objects offering common load functionality
    """
    # pylint: disable=no-member
    # no-member is disabled to force child classes to implement
    # the REQUIRED attribute describing a list of required
    # configuration keys

    _client = None
    _configuration = None

    @property
    def client(self):
        """
        Get the loaded manager client
        """
        return self._client

    @property
    def configuration(self):
        """
        Get the cofiguration object
            - load on demand
        """
        if self._configuration is None:
            self._configuration = Configuration()
        return self._configuration


    @accepts(str, str, must_implement=type)
    def _load(self, namespace, manager, must_implement=None):
        """
        Load the requested manager

        @param namespace string The namespace containing the managers ('pyccata.core')
        @param manager   string The name of the manager to load
        """
        namespace = namespace + '.managers.subjects.'
        try:
            module = importlib.import_module(namespace + manager.lower())
        except ImportError:
            raise InvalidModuleError(manager, namespace)
        try:
            name = getattr(module, manager.capitalize())
        except AttributeError:
            raise InvalidClassError(manager.capitalize(), namespace + manager.lower())

        if must_implement is not None and not implements(name, must_implement):
            raise ImportError('{0} must implement \'{1}\''.format(manager.capitalize(), must_implement))
        self.validate_configuration(manager.lower())
        self._client = name()

    @accepts(str)
    def validate_configuration(self, config_label):
        """
        Validates the configuration against the list of required attributes
        """
        if not hasattr(self, 'REQUIRED'):
            raise NotImplementedError('Objects inheriting <Manager> must implement a list of REQUIRED config elements')

        if config_label in Configuration.REPORTING_TYPES:
            config_label = 'report'
        configuration = getattr(Configuration(), config_label)
        for element in self.REQUIRED:
            if not hasattr(configuration, element):
                raise RequiredKeyError('{0}/{1}'.format(config_label, element))
        return True
