"""
Helper functions for decorators
"""
from weeklyreport.exceptions import InvalidArgumentNumberError
from weeklyreport.exceptions import ArgumentValidationError
from weeklyreport.helpers import implements

def ordinal(num):
    """
    Returns the ordinal number of a given integer, as a string.
    eg. 1 -> 1st, 2 -> 2nd, 3 -> 3rd, etc.
    """
    if 10 <= num % 100 < 20:
        return '{0}th'.format(num)
    else:
        ord_num = {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(num % 10, 'th')
        return '{0}{1}'.format(num, ord_num)

def validate_against_tuple(argument, inheritance):
    """
    if an argument can have a number of types,
    is the current argument type allowed?

    @param argument    mixed The argument to check
    @param inheritance tuple A set of argument types to verify against

    @return bool
    """
    valid = False
    for arg_type in inheritance:
        try:
            if argument is arg_type or isinstance(argument, arg_type) or implements(argument, arg_type):
                valid = True
                break
        except TypeError:
            pass
    return valid

def validate_positional_args(real_args, aargs, func):
    """
    Verifies the type provided to method arguments
    meets the type required by accepts

    @param real_args list     - arguments provided to the method
    @param aargs     list     - arguments found in the method accepts signature
    @param func      function - the bound function being validated

    @raise InvalidArgumentNumberError if the number of arguments provided does not
                                      match the number of arguments expected.
    @raise ArgumentValidationError    if the argument fails to validate
    """
    if len(real_args) != len(aargs):
        raise InvalidArgumentNumberError(func.__name__)
    for arg_num, (actual_arg, accepted_arg_type) in enumerate(zip(real_args, aargs)):
        ord_num = ordinal(arg_num + 1)
        if isinstance(accepted_arg_type, tuple):
            if not validate_against_tuple(actual_arg, accepted_arg_type):
                raise ArgumentValidationError(ord_num, func.__name__, accepted_arg_type, actual_arg)
        elif (not isinstance(actual_arg, accepted_arg_type)) and (not implements(actual_arg, accepted_arg_type)):
            raise ArgumentValidationError(ord_num, func.__name__, accepted_arg_type, actual_arg)
    return True

def validate_keyword_args(kwargs, akwargs, func):
    """
    Verifies the type provided to method arguments
    meets the type required by accepts

    @param real_args list - arguments provided to the method
    @param aargs     list - arguments found in the method accepts signature
    @param func      function - the bound function being validated

    @raise TypeError               if provided argument does not match against the
                                   provided tuple of types.
    @raise ArgumentValidationError if the argument fails to validate
    """
    for k in kwargs:
        if not akwargs.__contains__(k):
            continue
        if isinstance(akwargs[k], tuple):
            if not validate_against_tuple(kwargs[k], akwargs[k]):
                raise TypeError(
                    'Invalid argument \'{a}\' provided to \'{f}\'. Must be one of \'{v}\''.format(
                        a=k, f=func.__name__, v=akwargs[k]
                    )
                )
        elif not isinstance(kwargs[k], akwargs[k]) or not implements(kwargs[k], akwargs[k]):
            raise ArgumentValidationError(k, func.__name__, akwargs[k], kwargs[k])
    return True

