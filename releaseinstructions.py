"""
Primary module for generating release notes from Jira

@author Martin Proffitt <martin.proffitt@hpe.com>
@package weeklyreport

"""
import os
import re
import shutil
from collections import namedtuple
from datetime import datetime
from releaseessentials.document import DocumentController
from releaseessentials.helpers import mkzip
from releaseessentials.helpers import unzip
from releaseessentials.helpers import create_directory
from releaseessentials.resources import Replacements
from releaseessentials.log import Logger
from releaseessentials.exceptions import InvalidFilenameError

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
    _regex = re.compile('^([0-9]*)?_?(\w+-\d+)_([a-zA-Z]+)_([a-zA-Z]+)_(UP|DOWN)_([0-9]*)?_?(\w+).[a-zA-Z]+$')

    def __init__(self):
        """ initialise the ReleaseNote object """
        self._document_controller = DocumentController(self.CONFIGURATION)
        self._document_controller.add_callback('attachments', getattr(ReleaseInstructions, 'file_collator'))

    def build_document(self):
        """ Creates the document structure """
        try:
            self._document_controller.build()
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

        create_directory(destination)
        create_directory(up_dir)
        create_directory(down_dir)

        for attachment in attachments:
            if hasattr(ReleaseInstructions, attachment.extension.lower() + '_handler'):
                Logger().debug('Calling handler \'' + attachment.extension + '_handler\'')
                getattr(ReleaseInstructions, attachment.extension.lower() + '_handler')(
                    destination,
                    os.path.join(path, attachment.filename)
                )
        return mkzip(destination, os.path.join(path, package_name + '.zip'))

    @staticmethod
    def zip_handler(destination, filepath):
        temporary_directory = os.path.join(destination, 'temp')
        create_directory(temporary_directory)
        unzip(filepath, temporary_directory, flatten=True)

        sql_files = [filename for filename in os.listdir(temporary_directory) if re.search("^.*\.sql$", filename)]
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
            Logger().error(exception)

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

