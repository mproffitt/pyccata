from unittest import TestCase
from mock import patch
from ddt import data, ddt, unpack

from weeklyreport.decorators import accepts
from weeklyreport.exceptions import ArgumentValidationError, InvalidArgumentNumberError

"""
Stub classes for testing accept decorator
"""
class Bar(object):
    pass

class Foo(object):
    pass

class Bob(Bar):
    pass

class _DecoratorMock(object):

    @accepts(int, int)
    def foo_times_bar(self, foo, bar):
        return foo * bar

    @accepts(int)
    def not_enough_arguments(self, bar, foo):
        pass

    @accepts(name=Bar)
    def invalid_named_arguments(self, name=Bar()):
        pass

    @accepts((Bar, Bob))
    def invalid_name_for_tuple_in_required_args(self, name):
        pass

    @accepts(name=(Bar, Bob))
    def invalid_named_for_tuple_in_kwargs(self, name=Bar()):
        pass

    @accepts(int, int, int, int, int, int, int, int, int, int, int, int)
    def check_for_ordinal(a, b, c, d, e, f, g, h, i, j, k, l):
        pass

    @accepts(value=Bob)
    def check_for_type_exception(name=Foo):
        pass

    @accepts(int, int, name=Bar)
    def check_for_required_skip_remainder(self, i, j, name=None, foo=None):
        pass

    @accepts((int, Bar))
    def check_str_against_tuple(self, something):
        pass

"""
End stub classes
"""

class TestAcceptsDecorator(TestCase):
    def setUp(self):
        self._mock = _DecoratorMock()

    def test_foo_times_bar(self):
        self.assertEquals(4, self._mock.foo_times_bar(2, 2))

    def test_foo_times_bar_raises_argument_validation_error(self):
        with self.assertRaises(ArgumentValidationError):
            self._mock.foo_times_bar('hello', 4)

    def test_not_enough_arguments(self):
        with self.assertRaisesRegexp(InvalidArgumentNumberError, 'Invalid number of arguments for .*'):
            self._mock.not_enough_arguments(1, 2)

    def test_tuple_in_required_args(self):
        with self.assertRaisesRegexp(ArgumentValidationError, 'The .* argument of .*\(\) is not a .*\(got \'.*\'\)'):
            self._mock.invalid_name_for_tuple_in_required_args(Foo())

    def test_named_argument_is_invalid_type(self):
        with self.assertRaises(ArgumentValidationError):
            self._mock.invalid_named_arguments(name=Foo())

    def test_named_argument_raises_exception_if_type_doesnt_matche(self):
        with self.assertRaises(TypeError):
            self._mock.invalid_named_for_tuple_in_kwargs(name=Foo)

    def test_named_argument_validates_true(self):
        self._mock.invalid_name_for_tuple_in_required_args(Bar())

    def test_check_for_ordinal_matches_th(self):
        with self.assertRaises(ArgumentValidationError):
            self._mock.check_for_ordinal(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 'hello', 12)

    def test_accepted_args_doesnt_contain(self):
        self._mock.check_for_required_skip_remainder(1, 2, name=Bob(), foo=Foo())

    def test_for_type_error_if_invalid_named_argument_provided_to_accepts(self):
        with self.assertRaises(TypeError):
            self._mock.check_for_type_exception()

