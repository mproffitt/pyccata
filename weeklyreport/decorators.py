import inspect
from functools               import wraps
from weeklyreport.exceptions import InvalidArgumentNumberError, ArgumentValidationError

def __ordinal(num):
    '''
    Returns the ordinal number of a given integer, as a string.
    eg. 1 -> 1st, 2 -> 2nd, 3 -> 3rd, etc.
    '''
    if 10 <= num % 100 < 20:
        return '{0}th'.format(num)
    else:
        ord = {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(num % 10, 'th')
        return '{0}{1}'.format(num, ord)

def __validate_against_tuple(argument, inheritance):
    valid = False
    for arg_type in inheritance:
        if argument is arg_type or isinstance(argument, arg_type) or issubclass(type(argument), arg_type):
            valid = True
            break
    return valid




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
        @wraps(func)
        def wrapper(*args, **kwargs):
            # if this is a bound method, drop the first argument which will be `self`
            bound = hasattr(args[0], func.__name__)
            real_args = args if not bound else args[1:]
            if len(real_args) != len(aargs):
                raise InvalidArgumentNumberError(func.__name__)
            for arg_num, (actual_arg, accepted_arg_type) in enumerate(zip(real_args, aargs)):
                ord_num = __ordinal(arg_num + 1)
                if isinstance(accepted_arg_type, tuple):
                    if not __validate_against_tuple(actual_arg, accepted_arg_type):
                        raise ArgumentValidationError(ord_num, func.__name__, accepted_arg_type, actual_arg)
                elif not isinstance(actual_arg, accepted_arg_type):
                    raise ArgumentValidationError(ord_num, func.__name__, accepted_arg_type, actual_arg)

            valid_args = inspect.getargspec(func).args
            for arg in akwargs:
                if not arg in valid_args:
                    raise TypeError(
                        'Invalid argument \'{a}\' provided to accepts decorator for \'{f}\''.format(
                            a=arg, f = func.__name__
                        )
                    )

            for k in kwargs:
                if not akwargs.__contains__(k):
                    continue
                if isinstance(akwargs[k], tuple):
                    if not __validate_against_tuple(kwargs[k], akwargs[k]):
                        raise TypeError(
                            'Invalid argument \'{a}\' provided to \'{f}\'. Must be one of \'{v}\''.format(
                                a=k, f=func.__name__, v=akwargs[k]
                            )
                        )
                elif not isinstance(kwargs[k], akwargs[k]):
                    raise ArgumentValidationError(k, func.__name__, akwargs[k], kwargs[k])

            return func(*args, **kwargs)
        return wrapper
    return accepted

