""" module for embedding pictures into the document """
import os
from releaseessentials.abstract import ThreadableDocument
from releaseessentials.decorators import accepts
from releaseessentials.configuration import Configuration
from releaseessentials.managers.report import ReportManager
from releaseessentials.exceptions import ThreadFailedError
from releaseessentials.log import Logger

class Picture(ThreadableDocument):
    """ Base class for picture objects """
    # Standard page is 5.7 inches
    MAX_WIDTH = 5.7

    # widths are actually calculated in percent
    _width = 100
    _filename = ''
    _path = ''

    @property
    def width(self):
        """ Get the current width as a percentage of Picture.MAX_WIDTH """
        return (self.MAX_WIDTH / 100) * self._width

    @width.setter
    @accepts((int, float))
    def width(self, width):
        """
        Set the current width

        @param width float A numerical value between 0.00 and 100.00
        """
        if width < .0 or width > 100.0:
            raise AttributeError('\'width\' should be in range 0 - 100')
        self._width = width

    @property
    def filepath(self):
        """ Get the full path to file (including filename) """
        return os.path.join(self._path, self._filename)

    @accepts(filename=str, width=(int, float))
    def setup(self, filename='', width=100):
        """
        Sets up the current Picture
        """
        # pylint: disable=arguments-differ
        self._path = Configuration().report.datapath
        path = os.path.join(self._path, filename)
        if not os.access(path, os.R_OK):
            raise FileNotFoundError(
                'File \'{filename}\' does not exist in {path} or cannot be opened'.format(
                    filename=filename,
                    path=self._path
                )
            )
        self._filename = filename
        self.width = width

    def run(self):
        """ Not requried for this class so sets _complete to True """
        self._complete = True

    @accepts(ReportManager)
    def render(self, report):
        """ Render the picture into the report """
        Logger().info('Adding picture {0}'.format(self.title if self.title is not None else ''))
        if not self._complete:
            raise ThreadFailedError('Failed to render document. Has thread been executed?')
        report.add_picture(self.filepath, width=self.width)
