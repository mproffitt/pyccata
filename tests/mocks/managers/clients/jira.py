from pyccata.core.interface import ManagerInterface

class Jira(ManagerInterface):
    __implements__ = (ManagerInterface,)
    pass

    def configuration(self):
        pass

    def projects(self):
        pass

    def search_issues(self):
        pass

    def server(self):
        pass


