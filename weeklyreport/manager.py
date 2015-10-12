import importlib
from weeklyreport.interface     import ManagerInterface
from weeklyreport.decorators    import accepts
from weeklyreport.configuration import Configuration
from weeklyreport.exceptions    import InvalidModuleError, InvalidClassError

class ProjectManager(ManagerInterface):
    _configuration = None
    _client        = None

    def __init__(self):
        namespace = self.configuration.NAMESPACE
        self._load(namespace, self.configuration.manager)

    @property
    def client(self):
        return self._client

    @property
    def configuration(self):
        if self._configuration is None:
            self._configuration = Configuration()
        return self._configuration

    def projects(self):
        return self._client.projects()

    @accepts(search_query=str, max_results=(bool, int), fields=list)
    def search_issues(self, search_query= '', max_results = 0, fields = []):
        return self._client.search_issues(search_query=search_query, max_results=max_results, fields=fields)

    @accepts(str, str)
    def _load(self, namespace, manager):
        try:
            module = importlib.import_module(namespace + '.managers.' + manager.lower())
        except ImportError:
            raise InvalidModuleError(manager, namespace)
        try:
            name = getattr(module, manager.capitalize())
        except AttributeError:
            raise InvalidClassError(manager.capitalize(), namespace + '.managers.' + manager.lower())
        if not issubclass(name, ManagerInterface):
            raise ImportError('{0} must implement \'ManagerInterface\''.format(manager.capitalize()))
        self._client = name()

