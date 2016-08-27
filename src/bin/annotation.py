#!/usr/bin/env python3
"""
Primary module for generating release notes from Jira

@author Martin Proffitt <martin.proffitt@hpe.com>
@package pyccata.core

"""
from datetime import datetime
from pyccata.core.document import DocumentController

class Annotations(object):
    """
    Contains the structure for generating release notes
    by collating the issue ID, release note text and business
    representative for all issues assigned to the current
    fix version which are in state done but not in state
    rejected.
    """

    CONFIGURATION = 'bio.json'
    _document_controller = None
    _document_ready = False
    _document_title = 'Sequence Annotation'

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
        self._document_controller.save(self._document_title + ' ' + '.docx')

if __name__ == "__main__":
    annotations = Annotations()
    annotations.build_document()
    annotations.publish()

