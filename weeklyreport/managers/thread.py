"""
Thread manager module
"""
from weeklyreport.threading import Threadable
from weeklyreport.decorators import accepts
from weeklyreport.managers.project import ProjectManager
from weeklyreport.managers.query import QueryManager
from weeklyreport.interface import ObservableInterface
from weeklyreport.helpers import implements
from weeklyreport.exceptions import ArgumentValidationError

class ThreadManager(list):
    """
    The thread manager handles all threads raised by the application
    assigning them out to the query manager as appropriate
    """
    def __init__(self):
        super().__init__()
        self._managed_threads = 0
        self._projectmanager = ProjectManager()
        self._queuemanager = QueryManager()

    @accepts(Threadable)
    def append(self, item):
        if hasattr(item, 'projectmanager'):
            item.projectmanager = self._projectmanager

        if implements(item, ObservableInterface):
            try:
                # looks like a duck, smells like a duck, is it a duck?
                self._queuemanager.append(item)
            except (ArgumentValidationError, TypeError):
                # no? don't care.
                pass

        super().append(item)
