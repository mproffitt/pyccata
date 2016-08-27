from unittest import TestCase
from mock import patch
from ddt import data, ddt, unpack

from pyccata.core.interface import ViewWindowInterface
from pyccata.core.log import Logger
from pyccata.core.exceptions import ArgumentValidationError
import sys

@ddt
class TestLogger(TestCase):

    class _TestView(object):
        pass

    class _ValidView(object):
        __implements__ = (ViewWindowInterface,)

        def write(self, message):
            sys.stdout.write(message)

        def flush(self):
            sys.stdout.flush()

        def readline(self):
            return sys.stdin.readline().strip()


    def setUp(self):
        Logger._instance = None
        self.logger = Logger()

    def tearDown(self):
        Logger._instance = None
        self.logger = None

    def test_logger_stdout_raises_exception_if_stdout_is_invalid(self):
        with self.assertRaises(ArgumentValidationError):
            self.logger.stdout = TestLogger._TestView()

    def test_logger_stdout_raises_exception_if_stdin_is_invalid(self):
        with self.assertRaises(ArgumentValidationError):
            self.logger.stdin = TestLogger._TestView()

    @patch('sys.stderr')
    @data(
        (Logger.DEBUG,   'this is a test message'),
        (Logger.INFO,    'this is a test message'),
        (Logger.WARNING, 'this is a test message'),
        (Logger.ERROR,   'this is a test message'),
        (Logger.FATAL,   'this is a test message')
    )
    @unpack
    def test_log_method(self, level, message, mock_write):
        self.logger._view = mock_write
        self.logger.log(level, message)
        mock_write.write.assert_called_with(level + message + "\n")

    @patch('sys.stderr')
    @data(
        (Logger.DEBUG,   'this is a test message'),
        (Logger.INFO,    'this is a test message'),
        (Logger.WARNING, 'this is a test message'),
        (Logger.ERROR,   'this is a test message'),
        (Logger.FATAL,   'this is a test message')
    )
    @unpack
    def test_log_method_with_suppression(self, level, message, mock_write):
        self.logger._view = mock_write
        self.logger.suppress = True
        self.logger.log(level, message)
        assert not mock_write.write.called

    @patch('sys.stderr')
    def test_debug(self,mock_write):
        self.logger._view = mock_write
        self.logger.debug('this is a test message')
        mock_write.write.assert_called_with(Logger.DEBUG + 'this is a test message' + "\n")

    @patch('sys.stderr')
    def test_info(self, mock_write):
        self.logger._view = mock_write
        self.logger.info('this is a test message')
        mock_write.write.assert_called_with(Logger.INFO + 'this is a test message' + "\n")


    @patch('sys.stderr')
    def test_warning(self, mock_write):
        self.logger._view = mock_write
        self.logger.warning('this is a test message')
        mock_write.write.assert_called_with(Logger.WARNING + 'this is a test message' + "\n")

    @patch('sys.stderr')
    def test_error(self, mock_write):
        self.logger._view = mock_write
        self.logger.error('this is a test message')
        mock_write.write.assert_called_with(Logger.ERROR + 'this is a test message' + "\n")

    @patch('sys.stderr')
    def test_fatal(self, mock_write):
        self.logger._view = mock_write
        self.logger.fatal('this is a test message')
        mock_write.write.assert_called_with(Logger.FATAL + 'this is a test message' + "\n")

    @patch('sys.stdin')
    @patch('sys.stderr')
    def test_input(self, mock_write, mock_input):
        mock_input.readline.return_value = "5\n"
        self.logger._view  = mock_write
        self.logger._input = mock_input
        value = self.logger.input('please enter a number')
        mock_write.write.assert_called_with(Logger.INFO + 'please enter a number > ')
        self.assertEquals(value, '5')

    @patch('sys.stderr')
    def test_append(self, mock_write):
        self.logger._view = mock_write
        self.logger.append('.')
        mock_write.write.assert_called_with('.')

    def test_logger_doesnt_reinit_when_called_again(self):
        log = Logger(view=sys.stdout)
        self.assertEquals(sys.stderr, log._view)

    @patch('sys.stdin')
    @patch('sys.stdout')
    def test_input_with_custom_vids(self, mock_write, mock_input):
        mock_input.readline.return_value = "5\n"
        self.tearDown()
        self.logger = Logger(view=TestLogger._ValidView(), stdin=TestLogger._ValidView())

        value = self.logger.input('please enter a number')
        mock_write.write.assert_called_with(Logger.INFO + 'please enter a number > ')
        self.assertEquals(value, '5')


