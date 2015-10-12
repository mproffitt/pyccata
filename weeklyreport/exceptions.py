class ArgumentValidationError(ValueError):
    """
    Raised when the type of an argument to a function is not what it should be.
    """
    def __init__(self, arg_num, func_name, accepted_arg_type, actual_arg):
        self.error = 'The {0} argument of {1}() is not a {2} (got \'{3}\')'.format(arg_num, func_name, accepted_arg_type, actual_arg)

    def __str__(self):
        return self.error

class InvalidArgumentNumberError(ValueError):
    """
    Raised when the number of arguments supplied to a function is incorrect.
    Note that this check is only performed from the number of arguments
    specified in the validate_accept() decorator. If the validate_accept()
    call is incorrect, it is possible to have a valid function where this
    will report a false validation.
    """
    def __init__(self, func_name):
        self.error = 'Invalid number of arguments for {0}()'.format(func_name)

    def __str__(self):
        return self.error

class RequiredKeyError(ValueError):
    """
    Raised when a required configuration key has not been provided
    within the config file
    """
    def __init__(self, key):
        self.error = 'Invalid key. \'{0}\' cannot be found'.format(key)

    def __str__(self):
        return self.error

class InvalidClassError(ValueError):
    """
    Raised when trying to load a class dynamically
    """
    def __init__(self, class_name, namespace):
        self.error = '{0} does not exist in {1}'.format(class_name, namespace)

    def __str__(self):
        return self.error
