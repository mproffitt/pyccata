Pipeline application suite
===========================

This suite provides library functionality for supporting application release processes.

Key functionality
-----------------

* Ability to generate release notes from your project manager software
* Ability to generate release instructions for the SysOps team from your project manager software
* Ability to output the release note and release instructions in Microsoft word format optionally embedded in a single table cell for sending as an email body.

Road map
--------

### Version 1.3 [October/November 2016] ###
Version 1.3 of this application will see the following functionality included

* Documentation on how to write the config files including available and required fields
* Ability to generate future fix versions against the format you specify
* Ability to capture a 'helicopter' view of targetted specific projects, allowing for easy creation of project status reports
* Ability to output graphs
* Simple command pipeline runner (Bash commands)

### Version 1.4 [January 2017] ###
Version 1.4 of this application suite will see:

* Extended pipeline runner (direct `R` language inclusion using r2py)
* Integration to Jenkins for larger pipeline support

### Unplanned ###

* Integration to GIT
* Configuration file generation software

Basic setup
-----------
The suite requires a basic application binding to be provided - see the bin/ directory for examples of how to do this.

A JSON configuration file must also be provided for your application inside one of the following search paths:

* `${XDG_CONFIG_HOME}/releaseessentials`
* `/etc/releaseessentials`
* `<install_directory>/releasessentials/conf`

Requirements
------------

This application can only be executed with Python 3.4 or later and requires the following libraries:

* jira
* lxml
* cairosvg
* tinycss
* cssselect
* pygal
* numpy
* Pillow
* python-docx
* pyquery

Tests
-----
To execute the tests, you will further require:

* nose
* pbr
* mock
* ddt

Installation
------------
To install this application, the following system libraries are required:

* xz-devel
* libxml2
* libxml2-devel
* libjpeg-devel
* libcurl-devel
* Depending on how libcurl was compiled, you may also require one of:
  * nss-devel
  * openssl-devel
  * gnutls-devel
  * ssl-devel

Once installed, from the root of the JiraWeeklyReport directory, execute the following:

    python3 setup.py install

If installation aborts with the following error:

    Tk/tkImaging.c:396:5: error: ISO C90 forbids mixed declarations and code [-Werror=declaration-after-statement]

Use the following steps to resolve:

1) Clone the Pillow repo from https://github.com/python-pillow/Pillow:

    git clone https://github.com/python-pillow/Pillow.git

2) Open Tk/tkImaging.c and apply the following changes

    Line 374:
    -    PyObject *bytes = PyUnicode_EncodeFSDefault(fname);
    +    PyObject* bytes;
    +    bytes = PyUnicode_EncodeFSDefault(fname);

    Line 395:
    +    void* func;
         /* Reset errors. */
         dlerror();
    -    void *func = dlsym(lib_handle, func_name);
    +    func = dlsym(lib_handle, func_name);

3) Run setup.py to build and install from source instead of downloading

    python3 setup.py install

If the tests (see execution steps below) fail an error similar to the following:

    ImportError: pycurl: libcurl link-time ssl backend (nss) is different from compile-time ssl backend (openssl)

Uninstall pycurl then install the library listed as the link-time library, for example:

    pip3 uninstall pycurl
    [apt-get|dnf|yum] install -y nss-devel

Next, set an environment variable of `PYCURL_SSL_LIBRARY=<link_time_library>` and re-install pycurl

    PYCURL_SSL_LIBRARY=nss
    pip3 install pycurl

Tests
-----
To execute the tests, you will further require:

* nose
* pbr
* mock
* ddt

Tests can be executed by running the following command:

    python3 setup.py nosetests -s --with-coverage --cover-branches --cover-html --cover-package releaseessentials

This command will generate code coverage and place this in the `cover` directory in the module root.

Linting
-------
If you have PyLint installed, code quality can be obtained by running:

    pylint releaseessentials

Note: This configuration has been targetted for pylint 1.6.4 or later with Astroid 1.4.7 or later.

Lint configuration:

To avoid common warnings, set the following in your `~/.pylintrc`

    max-line-length=120
    disable=locally-disabled,abstract-class-not-used,maybe-no-member

You may also need to delete the following if they exist for pylint to stop complaining

    required-attributes
    ignore-iface-methods

Documentation
-------------
If Doxygen and graphviz are installed, API documentation can be generated by executing `doxygen` in the root of the module.

A Doxyfile has been provided for this purpose which will generate API documentation with class, collaboration, call and callee graphs embedded within.

Please note, this API is not complete although existing functionality is not expected to change.

Sample configuration
--------------------
The samples directory contains sample configuration files

Templates
---------

The following Microsoft Word template has been provided as an example:

* GreenTemplate.docx
  Top level headings are underlined in green, sub-headings are green and tables are outputted in green and white banding.

Contributions
-------------
Contributions are welcome although they must meet the following guidelines.

* All submitted branches must follow the GitFlow model (see http://nvie.com/posts/a-successful-git-branching-model/).
* 100% line and branch coverage must be produced - No code will be accepted unless this is the case.
* Code must meet the project guidelines.
  * Line length no greater than 120 characters.
  * Use of @accepts for all public methods.
  * If you disable pylint validation, you must provide a clear reason why as a comment on the line immediatly below the disable line.
* Overly complex code will not be accepted.

