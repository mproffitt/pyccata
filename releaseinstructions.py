"""
Primary module for generating release notes from Jira

@author Martin Proffitt <martin.proffitt@hpe.com>
@package weeklyreport

"""
from datetime import datetime
from releaseessentials.document import DocumentController

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
    _document_title = 'MSS Platform Release'

    def __init__(self):
        """ initialise the ReleaseNote object """
        self._document_controller = DocumentController(self.CONFIGURATION)

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

if __name__ == "__main__":
    release_instructions = ReleaseInstructions()
    release_instructions.build_document()
    release_instructions.publish()

