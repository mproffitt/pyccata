"""
Helper methods for the releaseessentials package
"""
import os
import importlib

def class_exists(namespace, module, class_name):
    """
    Test to see if the given class exists

    @param namespace  string
    @param module     string
    @param class_name string

    @return bool
    """
    try:
        module = importlib.import_module(namespace + '.' + module + '.' + class_name.lower())
    except ImportError:
        return False
    return hasattr(module, class_name.capitalize())

def implements(obj, interface):
    """
    Test to see if interface is defined by the given object

    @param obj       object
    @param interface Interface

    @return bool

    This test is carried out by first looking at the objects __implements__
    tuple. If ``__implements__`` is not defined, the check looks to see
    if ``obj`` extends ``interface``

    If neither of these checks succeed, False is returned
    """
    try:
        return interface in obj.__implements__
    except AttributeError:
        pass
    return issubclass(type(obj), interface)

def read_file(text_url, report_path=''):
    """
    When reading from a config file, the text may be
    specified as either a block of text or a url to a
    text file.

    Easiest is to pass the whole lot through to file
    and if a file doesn't exist with the content as name,
    return the text.

    @param text_url string

    @return string
    """
    path = os.path.join(report_path, text_url) + '.txt'

    if os.access(path, os.R_OK):
        with open(path) as file_pointer:
            return file_pointer.read()
    return text_url
