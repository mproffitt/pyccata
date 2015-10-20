"""
Thread manager module
"""
from time import sleep
from weeklyreport.threading import Threadable
from weeklyreport.decorators import accepts
from weeklyreport.managers.project import ProjectManager
from weeklyreport.managers.query import QueryManager
from weeklyreport.interface import ObservableInterface
from weeklyreport.helpers import implements
from weeklyreport.exceptions import ArgumentValidationError
from weeklyreport.exceptions import InvalidConnectionError
from weeklyreport.exceptions import InvalidQueryError
from weeklyreport.exceptions import PoolEmptyError
from weeklyreport.log import Logger
from weeklyreport.configuration import Configuration

class ThreadManager(list):
    """
    The thread manager handles all threads raised by the application
    assigning them out to the query manager as appropriate
    """

    # pylint: disable=too-many-instance-attributes
    # Due to the nature of the threadable class this
    # will always have too many attributes.

    POOL_SIZE = 10
    MAX_RETRIES = 3
    _instance = None
    _is_loaded = False

    def __init__(self):
        if self._is_loaded:
            return
        super().__init__()
        self._managed_threads = 0
        self._complete_threads = 0
        self._projectmanager = ProjectManager()
        self._querymanager = QueryManager()
        self._configuration = Configuration()
        self._failed_threads = []
        self._pool = []
        self._complete = False
        self._is_loaded = True

    @property
    def configuration(self):
        """ get the loaded configuration object """
        return self._configuration

    @property
    def projectmanager(self):
        """ get the project manager instance """
        return self._projectmanager

    @property
    def querymanager(self):
        """ get the query manager instance """
        return self._querymanager

    @property
    def completed(self):
        """ Have all threads executed successfully? """
        return self._complete

    @accepts(Threadable)
    def append(self, item):
        """
        Append a new Threadable item to the list of threads to execute
        """
        if hasattr(item, 'projectmanager'):
            item.projectmanager = self.projectmanager

        # looks like a duck, smells like a duck, is it a duck?
        if implements(item, ObservableInterface):
            try:
                self.querymanager.append(item)
            except ArgumentValidationError:
                # It's not??? Don't care.
                pass

        if not hasattr(item, 'observing') or not item.observing:
            super().append(item)
        self._managed_threads += 1

    def start(self):
        """ Sorts the list and then triggers execute, setting _complete on execute completion """
        self.sort(key=lambda x: x.PRIORITY, reverse=True)
        self._complete = self.execute()

    def execute(self):
        """
        Starts all threads in the current batch

        If a thread fails when other threads are observing it,
        the risk is that no threads will be able to obtain their
        results.

        This can happen for one of 2 reasons.
          1. A thread has been given an invalid query to run
             In this case, all threads should fail because they
             share the query.
          2. A network timeout has occurred (or the remote has failed)
             In this instance we want to retry with the other threads
             by taking the observers from the thread, appending the failed
             thread to the observers, taking the first observer and assigning
             all other threads to it as observers and then restarting until
             all threads within this batch have failed or one succeeds.
             Once any of the threads succeeds, the failure flag should be
             removed from all failed threads.
        """
        # fill up the pool
        self._fill_pool()

        while len(self._pool) > 0:
            self.monitor()
            try:
                self._fill_pool()
            except PoolEmptyError:
                pass
            sleep(Threadable.THREAD_SLEEP)
        if len(self._failed_threads) > 0:
            Logger().error('{0} threads have failed as part of this execution'.format(len(self._failed_threads)))
            return False
        return True

    def monitor(self):
        """
        Monitor pooled threads and remove complete and failed ones
        """
        for thread in self._pool:
            try:
                if not thread.isAlive():
                    self._pool.remove(thread)

                if thread.complete:
                    thread.join()

                if thread.failed:
                    raise thread.failure
            except InvalidQueryError:
                self._failed_threads.append(thread)
                self.remove(thread)
            except InvalidConnectionError:
                self.remove(thread)
                if not thread.hasobservers:
                    self._failed_threads.append(thread)
                else:
                    self.rotate_observers(thread)

    @accepts(Threadable)
    def rotate_observers(self, thread):
        """
        Rotates observers of a failed thread

        @param thread Threadable

        If a thread has failed because of a broken / lost connection but has observers,
        this method rotates the observers and tries again with a different thread.
        """
        observers = thread.observers
        observers.append(thread)
        replacement = observers[0]
        for item in observers[1:]:
            replacement.append(item)
        # if the replacement has already got a failure, we've exhausted the list
        # and cannot continue
        if replacement.failed:
            self._failed_threads.append(replacement)
            return
        super().append(replacement)

    def _fill_pool(self):
        """ Fills the current executing thread pool from the class pool """
        complete = True
        # dont bother filling the pool if there
        # is nothing left to fill it with
        for thread in self:
            if thread.ready:
                complete = False
                break
        if complete:
            raise PoolEmptyError()

        i = 0
        while i < len(self) and len(self._pool) < self.POOL_SIZE:
            thread = self[i]
            if thread.ready and thread not in self._pool:
                try:
                    thread.start()
                    self._pool.append(thread)
                # skip if thread has already been started
                except RuntimeError:
                    pass
            if i < len(self):
                i += 1

    def __new__(cls):
        """
        Override for __new__ to check if ThreadManager has already been loaded.
        """
        if cls._instance is None:
            Logger().debug('Loading singleton ThreadManager')
            cls._is_loaded = False
            cls._instance = super(ThreadManager, cls).__new__(cls)
        return cls._instance

