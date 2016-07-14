"""
Contains decorators in use within the application
"""
import inspect
from functools import wraps
from weeklyreport.decorator_helpers import validate_positional_args
from weeklyreport.decorator_helpers import validate_keyword_args

def accepts(*aargs, **akwargs):
    """
    Validates that the arguments provided to a method / function are of the correct type

    This method checks both args and keyword args for the respective types

    If a method parameter can be called with multiple types, these should be passed as a
    tuple to the accepts method.

    Example:
    <pre>
    class Bar(object):
        def __init__(self):
            self.foo = 'Hello world'
    class Bob(object):
        def __init__(self):
            self.foo = 'Goodbye'

    class Invalid(object):
        pass

    class Foo(object):
        @accepts(int, name=(Bar, Bob))
        def _init__(self, index, name = Bar()):
            self.index = index
            self.name  = name

    foo = Foo(1)            # valid - defaults to Bar()
    foo = Foo(1, Bob())     # valid - Bob class is in tuple for name
    foo = Foo(1, Invalid()) # raises Argument validation error
    </pre>
    Note:
        No deep checking is carried out. It is up to you to ensure that nested types are
        correct before `func` is called.
    """
    def accepted(func):
        """ Decorator """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """ decorator wrapper """
            # if this is a bound method, drop the first argument which will be `self`
            bound = hasattr(args[0], func.__name__)
            real_args = args if not bound else args[1:]
            validate_positional_args(real_args, aargs, func)

            #pylint: disable=deprecated-method
            # inspect.getargspec is not actually deprecated or likely to be removed:
            # @see https://bugs.python.org/issue25486
            valid_args = inspect.getargspec(func).args
            for arg in akwargs:
                if not arg in valid_args:
                    raise TypeError(
                        'Invalid argument \'{a}\' provided to accepts decorator for \'{f}\''.format(
                            a=arg, f=func.__name__
                        )
                    )
            validate_keyword_args(kwargs, akwargs, func)
            return func(*args, **kwargs)
        return wrapper
    return accepted
