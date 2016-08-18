"""
Module for managing attachments to issues

@package releaseessentials
@author Martin Proffitt <mproffitt@jitsc.co.uk>
@link https://bitbucket.org/mproffitt/jiraweeklyreport
@link https://esspde-gitlab.ssn.hpe.com/proffitt/JiraWeeklyReport
"""
import os
import pycurl
from releaseessentials.managers.report import ReportManager
from releaseessentials.abstract import ThreadableDocument
from releaseessentials.decorators import accepts
from releaseessentials.filter import Filter
from releaseessentials.resources  import Replacements
from releaseessentials.log import Logger
from releaseessentials.helpers import create_directory
from releaseessentials.configuration import Configuration
from releaseessentials.exceptions import InvalidCallbackError

class Attachments(ThreadableDocument):
    """
    Represents a list of ticket attachments for a release
    """

    _content = None
    _collate = None
    _output_path = None

    def setup(self, query, fields=None, collate=None, output_path='/tmp'):
        """ Set up the attachments object """
        # pylint: disable=arguments-differ
        self._content = Filter(query, max_results=50, fields=fields)
        self.threadmanager.append(self._content)
        self.projectmanager = Configuration().manager
        self._collate = collate.split(',')
        self._output_path = Replacements().replace(output_path)
        create_directory(self._output_path)

    def run(self):
        """ wait for the filter to complete """
        while not self._complete:
            self._complete = self._content.complete
            if self._content.failed:
                Logger().warning('Failed to execute ' + self._content.query)
                Logger().warning(self._content.failure)
                self._complete = True
                return

        content = [item for issue in self._content.results for item in issue.attachments]
        contents = []
        for collate in self._collate:
            contents.append(
                getattr(Attachments, collate)(content) if hasattr(Attachments, collate) else content
            )
        self._content = [item for content in contents for item in content]
        if len(self._content) == 0:
            Logger().warning('No Attachments to download. Skipping.')
            return

        try:
            self._download_attachments()
        except InvalidCallbackError as exception:
            Logger().error(exception)
            self.failure = exception


    def _download_attachments(self):
        """
        Downloads all attachments from the project manager.
        """
        # attachments function is a callback to the project manager
        attachments_function = self.projectmanager.server.attachments
        if not attachments_function or attachments_function is None:
            raise InvalidCallbackError('attachments callback function has not been set')

        for item in self._content:
            with open(os.path.join(self._output_path, item.filename), 'wb') as output_file:
                attachment_url = attachments_function(str(item.attachment_id), item.filename)
                Logger().info('Downloading file \'' + item.filename + '\' from \'' + attachment_url + '\'')
                curl_instance = pycurl.Curl()
                curl_instance.setopt(curl_instance.URL, attachment_url)

                curl_instance.setopt(curl_instance.WRITEDATA, output_file)
                curl_instance.perform()
                curl_instance.close()


    @accepts(ReportManager)
    def render(self, document):
        """
        Saves all attachments to the output path
        """
        callback = document.get_callback('attachments')
        filenames = None
        if callback is not None:
            filenames = callback(self._output_path, self._content)
            if not isinstance(filenames, list):
                filenames = [filenames]
        if filenames is not None:
            document.add_paragraph('The following file(s) have been attached to this document:')
            for item in filenames:
                document.add_list(str(item))

    #
    # DEDICATED FILTERS FOR ATTACHMENTS
    #

    @staticmethod
    @accepts(list)
    def sql(content):
        """ Filters SQL file extensions """
        return [item for item in content if item.extension.lower() == 'sql']

    @staticmethod
    @accepts(list)
    def zip(content):
        """ Filters zip file extensions """
        return [item for item in content if item.extension.lower() == 'zip']
