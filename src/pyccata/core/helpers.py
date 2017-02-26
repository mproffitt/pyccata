"""
Helper methods for the pyccata.core package
"""
import os
from datetime import date
import importlib
import zipfile
import shutil

from pyccata.core.exceptions import InvalidModuleError

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

def resource(class_name, namespace):
    """
    Loads a class from the resources module
    """
    return include(class_name, namespace, 'resources')

def collation(method_name, namespace):
    """
    Loads a method from the collation module
    """
    return include(method_name, namespace, 'collation')

def include(class_name, namespace, module_name):
    """
    Loads a class from `namespace`.resources

    if class doesn't exist in namespace, falls back to `pyccata.core`
    """
    try:
        module = importlib.import_module('pyccata.{0}.{1}'.format(namespace, module_name))
    except ImportError:
        module = importlib.import_module('pyccata.core.{0}'.format(module_name))
    if hasattr(module, class_name):
        return getattr(module, class_name)
    raise InvalidModuleError(
        class_name,
        '{0}.{1}'.format(namespace, module_name)
    )

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

def create_directory(directory):
    """
    Recursively creates a directory path if it doesn't already exist

    @param directory string
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def unzip(source_filename, dest_dir, flatten=False):
    """
    Unpack a zip file to the destination directory

    @param source_filename
    @param dest_dir
    @param flatten bool

    Function has been adapted from stack-overflow.
    @see http://stackoverflow.com/questions/12886768/how-to-unzip-file-in-python-on-all-oses

    If flatten is True, this will take all files from the zip and move them into dest_dir without
    including any child paths.
    """
    if flatten:
        return unzip_flat_dir(source_filename, dest_dir)

    with zipfile.ZipFile(source_filename) as zip_file:
        for member in zip_file.infolist():
            # Path traversal defense copied from
            # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
            words = member.filename.split('/')
            path = dest_dir

            for word in words[:-1]:
                while True:
                    drive, word = os.path.splitdrive(word)
                    word = os.path.split(word)[1]
                    if not drive:
                        break
                if word in (os.curdir, os.pardir, ''):
                    continue
                path = os.path.join(path, word)
            zip_file.extract(member, path)


def unzip_flat_dir(source_filename, dest_dir):
    """
    Unpack a zip file to a flattened directory structure
    """
    with zipfile.ZipFile(source_filename) as zip_file:
        for member in zip_file.namelist():
            filename = os.path.basename(member)
            if not filename:
                continue
            with zip_file.open(member) as source, open(os.path.join(dest_dir, filename), mode="wb") as target:
                shutil.copyfileobj(source, target)

def mkzip(directory, zip_name):
    """
    Zip up a given directory

    @param directory string
    @param zip_name string

    @return path to final zip file
    """
    cur_dir = os.getcwd()
    os.chdir(directory)
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # pylint: disable=unused-variable
        for root, dirs, files in os.walk('.'):
            for filename in files:
                zip_file.write(os.path.join(root, filename))
        zip_file.close()
        os.chdir(cur_dir)
        return zip_name

def modified_helper(path):
    """
    Get the date a path was modified

    :param string: path
    :returns: string YYYY-mm-dd
    :raises ValueError: if path does not exist
    """
    if os.path.exists(path):
        return date.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d')
    raise ValueError('Invalid path provided for modified date')
