#!/usr/bin/env python3
"""
Primary module for generating release notes from Jira

@author Martin Proffitt <martin.proffitt@hpe.com>
@package weeklyreport

"""
import os
import re
import requests
import shutil
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from collections import namedtuple
from datetime import datetime
from pyccata.core.document import DocumentController
from pyccata.core.helpers import mkzip
from pyccata.core.helpers import unzip
from pyccata.core.helpers import create_directory
from pyccata.core.resources import Replacements
from pyccata.core.log import Logger
from pyccata.core.exceptions import InvalidFilenameError

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ReleaseInstructions(object):
    """
    Contains the structure for generating release notes
    by collating the issue ID, release note text and business
    representative for all issues assigned to the current
    fix version which are in state done but not in state
    rejected.
    """

    CONFIGURATION = 'releaseinstructions.json'
    _document_controller = None
    _document_ready = False
    _document_title = 'MSS Platform Release Rollout and Rollback'
    _configuration = None
    _crumb = None

    _regex = re.compile(
        '^([0-9]*)?_?(\w+-\d+)_([a-zA-Z-]+)_(\w+)_(UP|DOWN)_([0-9]*)?_?(\w+)(.[a-zA-Z]+)?$',
        re.IGNORECASE
    )

    def __init__(self):
        """ initialise the ReleaseNote object """
        self._document_controller = DocumentController(self.CONFIGURATION)
        self._configuration = self._document_controller.configuration
        self._document_controller.add_callback('attachments', getattr(ReleaseInstructions, 'file_collator'))

    def build_document(self):
        """ Creates the document structure """
        try:
            self._document_controller.build()
            final = Replacements().find('FINAL').value
            if final in ['1', 'True', 'TRUE', 'true']:
                pipelines = self._document_controller.threadmanager.find('MSS Deployment Pipelines')
                if pipelines is not None and len(pipelines) > 0:
                    for pipeline in pipelines:
                        self.pipeline_trigger(pipeline)
            self._document_ready = True
        except:
            self._document_ready = False
            raise

    def publish(self):
        """ publish the document """
        if not self._document_ready:
            self.build_document()

        date = datetime.strftime(datetime.now(), '%Y-%m-%d')
        self._document_controller.format_for_email()
        self._document_controller.save(self._document_title + ' ' + date + '.docx')

    def pipeline_trigger(self, pipeline):
        """
        Triggers a pipeline on Jenkins

        FUTURE - move out to Jenkins API wrapper
        """
        replacements = Replacements()
        pipeline = replacements.replace(pipeline)
        matches = re.search(r'(http.*\/).*', pipeline)
        if matches:
            pipeline = matches.groups(0)[0].rstrip('/')

        authentication = HTTPBasicAuth(
            self._configuration.jenkins.user,
            self._configuration.jenkins.password
        )

        if not self._crumb:
            endpoint = '{server}/crumbIssuer/api/json'.format(
                server=self._configuration.jenkins.server.strip('/')
            )

            response = requests.get(
                endpoint,
                auth=authentication,
                verify=False
            )
            self._crumb = json.loads(response.text)['crumb']

        Logger().info('Triggering pipeline {0}'.format(pipeline))
        params = {}
        auth = (self._configuration.jenkins.user, self._configuration.jenkins.password)
        pipeline = '{0}/{1}'.format(pipeline, replacements.replace('{TRIGGER_URI}'))
        response = requests.post(
            pipeline,
            auth=auth,
            params=params,
            verify=False,
            headers={"Jenkins-Crumb": self._crumb},
        )
        if response.status_code != 200:
            Logger().error(
                'Error whilst triggering pipeline - server returned status {0}'.format(
                    response.status_code
                )
            )
        Logger().info('Done {0}'.format(pipeline))

    @staticmethod
    def file_collator(path, attachments):
        """
        This method unpacks all zip files and copies the resulting SQL into a temporary location

        Once complete, it repackages the temporary location and moves it into the Workspace for
        attachment to the release instruction email
        """
        Logger().info('Collating SQL files from attachments')
        package_name = Replacements().replace('mss-platform-release-{FIX_VERSION}').replace('/', '-')
        destination = os.path.join(path, package_name)
        up_dir = os.path.join(destination, 'up')
        down_dir = os.path.join(destination, 'down')
        package_dir = os.path.join(os.getcwd(), 'packages')
        if not os.path.exists(package_dir):
            create_directory(package_dir)

        create_directory(destination)
        create_directory(up_dir)
        create_directory(down_dir)

        for attachment in attachments:
            if hasattr(ReleaseInstructions, attachment.extension.lower() + '_handler'):
                filename = os.path.join(path, attachment.filename)
                Logger().debug(
                    'Calling handler \'' + attachment.extension + '_handler\' for file ' + filename
                )

                try:
                    getattr(ReleaseInstructions, attachment.extension.lower() + '_handler')(
                        destination,
                        os.path.join(path, attachment.filename)
                    )
                except Exception as exception:
                    Logger().error('Failed to add file \'' + filename + '\' to archive')
                    Logger().error('reason: ' + str(exception))

        filename = mkzip(destination, os.path.join(path, package_name + '.zip'))
        shutil.move(os.path.join(destination, filename), os.path.join(package_dir, os.path.basename(filename)))
        return os.path.basename(filename)

    @staticmethod
    def zip_handler(destination, filepath):
        temporary_directory = os.path.join(destination, 'temp')
        create_directory(temporary_directory)
        unzip(filepath, temporary_directory, flatten=True)

        sql_files = [
            filename for filename in os.listdir(
                temporary_directory
            ) if re.search(
                "^.*\.sql$", filename, re.IGNORECASE
            )
        ]
        if len(sql_files) == 0:
            Logger().error('Got zip file but it contains no SQL files. Skipping...')
        for sql in sql_files:
            ReleaseInstructions.sql_handler(destination, os.path.join(temporary_directory, sql))
        shutil.rmtree(temporary_directory)

    @staticmethod
    def sql_handler(destination, filepath):
        try:
            Logger().info('Adding file \'' + filepath + '\'')
            sql_file = ReleaseInstructions._sql_filename(os.path.basename(filepath))
            output_directory = os.path.join(
                destination,
                sql_file.direction.lower(),
                sql_file.ticket_order,
                sql_file.ticket_id,
                sql_file.server,
                sql_file.database
            )
            create_directory(output_directory)
            os.rename(
                filepath,
                os.path.join(
                    output_directory,
                    (
                        sql_file.operation_order + '_' if sql_file.operation_order is not None else ''
                    ) + sql_file.operation + '.sql'
                )
            )

        # pylint: disable=broad-except
        # We are not bothering to handle invalidly named SQL files - these will be
        # ignored from the instruction sent to SysOps.
        # ANY error here and the file gets bounced back to the developer.
        except Exception as exception:
            Logger().error('Failed to handle SQL file \'' + os.path.basename(filepath) + '\'')
            Logger().error('reason: ' +  str(exception))

    @staticmethod
    def _sql_filename(filename):
        SQLStructure = namedtuple(
            'SQLStructure',
            'ticket_order ticket_id server database direction operation_order operation'
        )

        try:
            groups = ReleaseInstructions._regex.search(filename).groups()
            return SQLStructure(
                ticket_order=(groups[0] if groups[0] != '' else 'any_order'),
                ticket_id=groups[1],
                server=groups[2],
                database=groups[3],
                direction=groups[4],
                operation_order=(groups[5] if groups[5] != '' else None),
                operation=groups[6]
            )
        except AttributeError:
            raise InvalidFilenameError('The filename \'' + filename + '\' does not match the anticipated format')

if __name__ == "__main__":
    release_instructions = ReleaseInstructions()
    release_instructions.build_document()
    release_instructions.publish()

