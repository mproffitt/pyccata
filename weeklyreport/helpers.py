import os
import sys
import importlib
from collections            import namedtuple
from weeklyreport.log       import Logger
from weeklyreport.interface import ManagerInterface

def class_exists(namespace, module, class_name):
    try:
        module = importlib.import_module(namespace + '.' + module + '.' + class_name.lower())
    except ImportError:
        return False
    name = getattr(module, class_name.capitalize())
    if not issubclass(name, ManagerInterface):
        raise ImportError('{0} must implement \'ManagerInterface\''.format(class_name))
    return True

def read_file(text_url):
    """
    When reading from a config file, the text may be
    specified as either a block of text or a url to a
    text file.

    Easiest is to pass the whole lot through to file
    and if a file doesn't exist with the content as name,
    return the text...
    """
    if os.access(text_url, os.R_OK):
        with open(text_url) as fp:
            return fp.read()
    return text_url

