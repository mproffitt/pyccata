"""
Application package exceptions

"""
class ArgumentValidationError(ValueError):
    """
    Raised when the type of an argument to a function is not what it should be.
    """
    def __init__(self, arg_num, func_name, accepted_arg_type, actual_arg):
        self.error = 'The {0} argument of {1}() is not a {2} (got \'{3}\')'.format(
            arg_num,
            func_name,
            accepted_arg_type,
            actual_arg
        )
        super().__init__(self.error)

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
        super().__init__(self.error)

    def __str__(self):
        return self.error

class RequiredKeyError(ValueError):
    """
    Raised when a required configuration key has not been provided
    within the config file
    """
    def __init__(self, key):
        self.error = 'Invalid key. \'{0}\' cannot be found'.format(key)
        super().__init__(self.error)

    def __str__(self):
        return self.error

class InvalidClassError(ValueError):
    """
    Raised when trying to load a class dynamically
    """
    def __init__(self, class_name, namespace):
        self.error = '{0} does not exist in {1}'.format(class_name, namespace)
        super().__init__(self.error)

    def __str__(self):
        return self.error

class InvalidModuleError(ValueError):
    """
    Raised when trying to load a module dynamically
    """
    def __init__(self, module, namespace):
        self.error = '{0} does not exist in {1}'.format(module, namespace)
        super().__init__(self.error)

    def __str__(self):
        return self.error

class InvalidConnectionError(Exception):
    """
    Raised whilst trying to set up a connection to a 3rd party service
    """
    def __init__(self, code, server, message, headers=None):
        self._code = code
        self._error = message
        self._server = server
        self._headers = headers
        super().__init__(self._error)

    def __str__(self):
        message = "Recieved HTTP/{code} whilst establishing connection to {server}\n\n".format(
            code=self._code,
            server=self._server
        )
        message += 'Message was: \'{message}\''.format(message=self._error)
        return message

class InvalidQueryError(ValueError):
    """
    Raised when a search query fails
    """
    def __init__(self, message):
        self.error = message
        super().__init__(self.error)

    def __str__(self):
        return self.error
