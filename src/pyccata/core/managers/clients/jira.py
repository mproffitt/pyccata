""" Wrapper class onto python-jira """
import os
import re
import urllib.parse
from collections import namedtuple
from pyccata.core.decorators import accepts
from pyccata.core.abstract import ManagableAbstract
from pyccata.core.log import Logger
from pyccata.core.exceptions import InvalidConnectionError
from pyccata.core.exceptions import InvalidQueryError
from pyccata.core.resources import ResultList
from pyccata.core.resources import Issue
from pyccata.core.resources import Attachment

from jira.client import JIRA
from jira.exceptions import JIRAError

class Jira(ManagableAbstract):
    """ Jira management and searching class """

    REQUIRED = [
        'server',
        'port',
        'username',
        'password'
    ]

    def __init__(self):
        """ Initialise Jira """
        Logger().info('Initialising Jira interface')
        if self.configuration.jira.port != '':
            self._options['server'] = self.configuration.jira.server + ':' + self.configuration.jira.port
        else:
            self._options['server'] = self.configuration.jira.server

        # explicitly turn error log files off
        JIRAError.log_to_tempfile = False

    @property
    def server(self):
        """
        Get callback information for the Jira server
        """
        server = namedtuple('Server', 'server_address, attachments')
        return server(
            server_address=self._options['server'],
            attachments=getattr(self, '_attachment_url')
        )

    @property
    def client(self):
        """
        Lazy load the python-jira.client.JIRA object

        @return JIRA
        """
        if self._client is None:
            Logger().info('Establishing JIRA Api connection...')
            try:
                self._client = JIRA(
                    options=self._options,
                    basic_auth=(
                        self.configuration.jira.username,
                        self.configuration.jira.password
                    )
                )
                Logger().info('Connection success')
            except JIRAError as exception:
                Logger().error(
                    'Recieved HTTP/{code} whilst establishing connection to {server}'.format(
                        code=exception.status_code,
                        server=self._options['server']
                    )
                )
                Logger().error('Message was: \'{message}\''.format(message=exception.text))
                raise InvalidConnectionError(
                    exception.status_code,
                    self._options['server'],
                    exception.text,
                    exception.headers
                )
        return self._client

    @accepts(search_query=str, max_results=(bool, int), fields=(None, list), group_by=(None, str))
    def search_issues(self, search_query='', max_results=0, fields=None, group_by=None):
        """
        Search for issues in JIRA

        @param search_query string     A JQL formatted query
        @param max_results  [int|bool] If false will load all issues in batches of 50
        @param fields       list       A list of fields to include in the results

        @return ResultSet
        """
        # pylint: disable=unused-argument
        # The group_by argument is required by other clients
        # but will never be used within this class
        try:
            if isinstance(fields, list):
                fields = ','.join(fields)
            max_results = max_results if max_results != 0 else Jira.MAX_RESULTS
            results = self.client.search_issues(search_query, maxResults=max_results, fields=fields)
            Logger().debug('Got \'' + str(len(results)) + '\' results for query ' + search_query)
            return Jira._convert_results(results)
        except JIRAError as exception:
            expression = '.*Error in the JQL Query.*'
            if exception.status_code == 400 and re.match(expression, exception.text):
                raise InvalidQueryError(str(exception))
            raise InvalidConnectionError(
                exception.status_code,
                self._options['server'],
                exception.text,
                exception.headers
            )

    @accepts((str, int), str)
    def _attachment_url(self, attachment_id, filename):
        """
        Call back method for formatting the Attachment URL

        @param attachment_id string|int
        @param filename      string

        @return a valid URL to an attachment
        """
        return self._options['server'] + '/secure/attachment/' + attachment_id + '/' + urllib.parse.urlencode(
            {'': filename}
        ).strip('=')

    def projects(self):
        """ Get a list of all projects defined in Jira """
        return self.client.projects()

    @staticmethod
    @accepts(list)
    def _convert_results(results):
        """
        Converts a ``jira.client.ResultList`` of ``jira.resources.Issues`` into a
        ``pyccata.core.resources.ResultList`` of ``pyccata.core.resources.Issues``
        """
        result_set = ResultList()
        result_set.total = results.total if hasattr(results, 'total') else len(results)
        for issue in results:
            item = Issue()
            item.key = getattr(issue, 'key') if hasattr(issue, 'key') else None
            item.summary = getattr(issue.fields, 'summary') if hasattr(issue.fields, 'summary') else None
            item.issuetype = getattr(issue.fields, 'issuetype') if hasattr(issue.fields, 'issuetype') else None
            item.created = getattr(issue.fields, 'created') if hasattr(issue.fields, 'created') else None
            item.updated = getattr(issue.fields, 'updated') if hasattr(issue.fields, 'updated') else None
            item.priority = getattr(issue.fields, 'priority') if hasattr(issue.fields, 'priority') else None
            item.description = getattr(issue.fields, 'description') if hasattr(issue.fields, 'description') else None
            item.status = getattr(issue.fields, 'status') if hasattr(issue.fields, 'status') else None
            item.project = getattr(issue.fields, 'project') if hasattr(issue.fields, 'project') else None
            item.fixVersions = getattr(issue.fields, 'fixVersions') if hasattr(issue.fields, 'fixVersions') else None
            item.resolution = getattr(
                issue.fields, 'resolution'
            ) if hasattr(issue.fields, 'resolution') else None
            item.resolutiondate = getattr(
                issue.fields, 'resolutiondate'
            ) if hasattr(issue.fields, 'resolutiondate') else None
            item.creator = getattr(issue.fields, 'creator') if hasattr(issue.fields, 'creator') else None
            item.assignee = getattr(issue.fields, 'assignee') if hasattr(issue.fields, 'assignee') else None
            item.attachments = Jira._get_attachments(
                getattr(issue.fields, 'attachment') if hasattr(issue.fields, 'attachment') else None
            )
            item.release_text = getattr(
                issue.fields, 'customfield_10600'
            ) if hasattr(
                issue.fields, 'customfield_10600'
            ) else None
            item.business_representative = getattr(
                issue.fields, 'customfield_10700'
            ) if hasattr(
                issue.fields, 'customfield_10700'
            ) else None
            item.rollout_instructions = getattr(
                issue.fields, 'customfield_10800'
            ) if hasattr(
                issue.fields, 'customfield_10800'
            ) else None
            item.rollback_instructions = getattr(
                issue.fields, 'customfield_10801'
            ) if hasattr(
                issue.fields, 'customfield_10801'
            ) else None

            if hasattr(issue.fields, 'customfield_10802'):
                item.pipelines = [item.value for item in getattr(issue.fields, 'customfield_10802')]

            result_set.append(item)
        return result_set

    @staticmethod
    @accepts((list, None))
    def _get_attachments(attachments):
        """
        Formats the Jira attachments into pyccata.core attachment type

        @param attachments list
        """
        result_set = []
        if attachments is not None:
            for attachment in attachments:
                item = Attachment()
                item.filename = attachment.filename
                item.attachment_id = attachment.id
                item.mime_type = attachment.mimeType
                item.extension = os.path.splitext(attachment.filename)[1][1:].strip()
                result_set.append(item)
        return result_set
