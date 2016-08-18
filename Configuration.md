Configuration Files
================
The configuration files for the Release Essentials package is a JSON structure which contains details of the report to build.

This document outlines the key elements and their required fields.

Top level
---------------
**manager** `string` [Required]
     The manager element dictates which project management back end to use.
     The value of the manager must be the name of a module under `releaseessentials/managers/subjects` which implements `ManagerInterface`
     At present, the only valid value for here is `jira`

**reporting** `string` [Required]
     The reporting element determines the format to output the report.
     The value of `reporting` must be the name of a module under `releaseessentials.managers.subjects` which implements `ReportingInterface`
     At present, the only valid value for here is `docx`.

**modules** `list` [Required] [deprecated]
       A list of modules available to the application

**[manager_name]** `object` [required]
     This element should be replaced with the id of the manager being utilised, for example if the manager is set to `jira`, this block would have the key of `jira`

**Example**

         "manager": "jira",
         "jira": {}

**replacements** `list` [optional]
A list of replacements to make throughout the document. May optionally provide options for the command line


**report** `object` [required]
The report element contains the structure of the document.

Manager object
-------------------------
The manager object name will always have the key of the manager described in the `manager` element.

This object contains a structure for the logon and server credentials, as well as any optional values you wish to utilise within your manager.

The default manager provided is `jira` (file `releaseessentials.managers.subjects.jira`).

The following keys are required by the manager.

* **username** `string` [required]
* **password** `string` [required]
* **server** `string` [required]
* **port** `string` [required]

### Targeted for 1.3 ###
The following key is targeted for the 1.3 release of the library

* **customfields** `list` [required]

The custom fields key will contain a list of custom fields and how they map inside the
`releaseessentials.resources.Issue` class

At present, this is a hard-coded value but due to their nature of changing per-installation, these need to be configurable.

Each entry in this list will take the following form:

    {
        "identifier": "<releaseessentials.resources.Issue.field_name>",
        "name": "<Jira field descriptor>",
        "mapto": "<Jira field ID>"
    }

Within this block, the `releaseessentials.resources.Issue.field_name` is a fixed identifier which should not be changed.

`name`  and `mapto` come directly from Jira and describe the custom field whereby `name` is the Jira name of the custom field and `mapto` is it's related ID.

> To find the ID of a particular custom field, follow the instructions here:
https://answers.atlassian.com/questions/102822/how-can-i-find-the-id-of-a-custom-field-in-jira-5

For example if your custom field name is *Release Text* and it's custom ID is *10800* then the following entry would be made in the `customfields` list:

    "customfields": [
        {
            "identifier": "release_text",
            "name": "Release Text",
            "mapto": "customfield_10800"
        }
    ]

#### Required entries
The following entries are required within the `customfields` block.

    "customfields": [
        {
            "identifier": "release_text",
            "name": "",
            "mapto": ""
        },
        {
            "identifier": "business_representative",
            "name": "",
            "mapto": ""
        },
        {
            "identifier": "rollout_instructions",
            "name": "",
            "mapto": ""
        },
        {
            "identifier": "rollback_instructions",
            "name": "",
            "mapto": ""
        },
        {
            "identifier": "pipelines",
            "name": "",
            "mapto": ""
        }
    ]

Replacements
-----------------------
An entry in the Replacements list determines a textual replacement to make within the generated document. Once defined, replacements can be made by placing `{IDENTIFIER}` inside the string being rendered.

A string can contain any number of replacements and may also reference environment variables.

A replacement entry is made up of the following keys:

* **name** `string` [required]
* **type** `mixed` [required]
* **value** `string` [required]
* **overridable** `object` or `false` [required]

**type**
The type of replacement can reference any static method within the
`releaseessentials.resources.Replacements` class as well as being a primitive type.

Primitives are:
* `string`
* `int`
* `bool`
* `float`.

Presently the following methods also exist for **type**

* `csv` - Splits a comma separated string and replaces the last comma with *and*
* `release_date` - Formats a date string to the release date
* `fix_version` - Formats a date string to find the fix version based on the format `%Y-%m-%d`

**overridable**
If an replacement is overridable, it will take arguments from the command line.

To enable this, set the overridable flag to be a JSON object with the following keys:

* **flag** `string` [required] Long option string.
* **abbrev** `string` [required] a short option string.
* **required** `bool` [required] Not used at present.

**Example**

    "replacements": [
        {
            "name": "FIX_VERSION",
            "type": "fix_version",
            "value": "%Y-%m-%d",
            "overridable": {
                "flag": "--fix-version",
                "abbrev": "-f",
                "required": false
            }
        }
    ]

Report
-----------
The report element describes how the report is to look.

In general, the report is made up from the following entries:

* **title** `string` [required]
* **subtitle** `string` [optional]
* **abstract** `string` [optional]
* **path** `string` [required]
* **datapath** `string` [required]
* **template** `string` [required]
* **board_id** `int` [required]
* **sections** `list` [required]

### title
The title of your report or document

### subtitle
An optional subtitle for your document. - May be empty

### abstract
A short paragraph describing the purpose of the report. - May be empty

### path
Unused but should describe the output location of the documents - currently written to the current folder / work-space

### datapath
A path to look in for section content

### template
The template file for outputting the reports to.

> **A note about Microsoft docx templates.**
> When generating a template for use within the report software, it must contain a number of pre-defined styles. Many of these are user-defined as part of the configuration file, destined to target specific styles within the document template.
>
> When targeting a Microsoft default style, the `python-docx` library used to pick them up does not know how to interpret them unless a custom style element exists in the document structure for that particular default style.
>
> To overcome this, for each default style you target, open it inside Microsoft word, make a minor change to it, then save the document.
>
> The provided `GreenTemplate` sample contains styling for the following elements:
>

> 1. Light Shading Accent 6 (Table style)
> 2. Grid Table 4 Accent 6 (Table style)
> 3. ListBullet (List style)
> 4. ListNumber (List style)
> 5. Headings 1 - 5

#### Board ID
Depending on your `manager` this item may or may not be mandatory. For Jira it is. This is a configured Jira board against which all queries will be executed. It makes it easy to filter out certain projects which may be surplus to the report you are generating.

### sections
A section entry comprises of the following elements

* **title** `string` [required]
* **abstract** `string` [required - may be empty]
* **level** `int` The heading level to use
* **structure** `list` [required - may be empty]

#### Filter objects
Many Section items accept a structure from which a Filter is created. The structure of this filter is as follows:

* **query** `string` [required]
      A Query which can be executed by the `manager` back-end, for example a JQL query when using Jira as the back-end.
* **fields** `list` [required]
      A list of fields to return from the query result set.
* **collate** `string` or `object` [optional]
     If defined, must be a callback method on the calling class.
* **max_results** `int` [optional]
     The maximum number of results to return from a query - default returns everything.
* **distinct** `bool` [optional]
     If true, returns a set of items rather than a list. Only used inside collation methods which return a list.

**collate** must be a valid function inside the `releaseessentials.collation` module (see below) and is defined either as a string or as an object as such:

**String based**

    "collate": "<collation_name>"

**Object based**

    "collate": {
        "method": "<collation_name>",
        "field": "<releaseessentials.resources.Issue.property>"
    }

At present, the following methods are defined as collation callbacks.

**String based**

* **average_days_since_creation** (returns string, e.g. `'716 days'`)
* **average_duration** (returns string, e.g. `'716 days'`)
* **priority** (returns `namedtuple('Priority', 'critical medium high low lowest')`)
* **flatten** (returns a list)
* **project** (returns list of issues grouped by project)

**Object based**

* **total_by_type** (returns list of `namedtuple('Total', 'name value')(name=type, value=int)`)
* **assignee** (returns list of issues grouped by assignee)
* **weekly**

##### Extending the collation
A large part of the power within this application set comes from the power of being able to manipulate the results returned from the filter object by means of collation.

Collation takes a set of results and performs operations against it to retrieve only certain parts of the data, or information about the data-set.

Adding your own collation methods is fairly easy. Simply place a new function inside the `releaseessentials.collation` module which accepts a `releaseessentials.resources.ResultList` item as its only argument. For example:

    @accepts(ResultList)
    def my_collation_method(results):
        pass

If you wish to contribute your collation methods back to the trunk, you must ensure 100% line and branch coverage. See the **contributing** section of the README.md file for more information on how to contribute.

> Note. use of `@accepts` is not mandatory but advisable within this library.

That's it. Your new collation method is now available to use within your configuration files:

    {
        "type": "table",
        "content": {
            "title": "General statistics",
            "style": "Grid Table 4 Accent 6",
            "columns": [
                "",
                "value"
            ],
            "rows": {
                "query": "my collation query",
                "fields": [
                    "key",
                    "summary",
                    "priority"
                ],
                "collate": "my_collation_method"
            }
        }
    }

> **A note about rendering**
> When rendered as a table, each item in the collation return will be rendered in a single cell. When rendered as a list, each item will be a list element, etc..
> It is up to you what is returned from your collation method and how it is presented. The advise is, if your method returns a string, float or integer value, use multiple queries to present the data in an understandable fashion.
>
> Because collation methods operate on the result set from a Filter object, their functionality is shared amongst any structure which can accept a Filter (Table, List, Graph, etc.).

#### Section structure

The `structure` element describes how each section will look with a structure element mapping to a class in the `releaseessentials.parts` module which extends the `releaseessentials.abstract.ThreadableDocument` class.

The fields required for the content element in a structure item are formed from the `setup` method `**kwarg` arguments with the primary elements being described below.

Each element in the structure must have the following structure:

* **type** `string` [required]
* **title** `string` [optional]
* **content** `mixed` [required]

**type** must map to one of the document classes and may be one of:
* paragraph
* list
* table
* section

**title** Only list, section and table types accept the title key.
**content** Is an object describing the content of the current item.

##### Paragraph

A paragraph may be formed in one of three ways.

1. A single string describing the paragraph
2. A path to a file which can be opened by pythons built in `open` function - This must be a path under the path described in the `datapath` element.
3. A list of strings and objects which form a run.

> A paragraph is not threaded - therefore it cannot be formed from a filter.


**Examples**

1 - Plain text

    {
        "type": "paragraph",
        "content": {
            "text": "This is paragraph text"
        }
    }

2 - Url

    {
        "type": "paragraph",
        "content": {
            "text": "my_report/paragraph_1.txt"
        }
    }

3 - List of run elements

    {
        "type": "paragraph",
        "content": {
            "text": [
                "This is the start of a paragraph ",
                {
                    "style": "bold",
                    "text": "followed by some bold text, "
                }
                "followed by some plain text ",
                {
                    "style": "italic",
                    "text": "followed by some italic text."
                }
            ]
        }
    }

##### List
A list can either be formed from a plain list of text items or a filter which returns a single column and may optionally accept a title.

The `content` field is an object which describes the list.

**Fields**

* **style** `string` One of `ordered`, `unordered`
* **field** `string` [required] When using a filter, only looks at the field listed here.
* **content** `object` or `list`
If `content` is a list, elements in the list will be treated as list literals. If instead it's an object, it will be treated as a `releaseessentials.filter.Filter` object.


**Plain text example**

    {
        "type": "list",
        "title": "This is an example list",
        "content": {
            "style": "ordered",
            "field": "",
            "content": [
                "This is entry 1",
                "This is entry 2",
                "This is entry 3"
            ]
        }
    }

**Example using a Filter object**

    {
        "type": "list",
        "content": {
            "style": "unordered",
            "field": "pipelines",
            "content": {
                "query": "fixVersion = {FIX_VERSION} and 'Pipelines' is not empty and status = 'Done'",
                "fields": ["pipelines"]
            }
        }
    }

##### Table
The structure of a table is similar to that of a list whereby the content may come from either static text or be generated from a Filter object. Unlike lists however, your table may be a mix of both text and filters.

The `content` field is an object which describes the table.

**Fields**

* **style** `string` One of `ordered`, `unordered`
* **columns** `list`
* **rows** `list`

If `rows` is a list of plaintext items, elements in the list will be treated as cell literals. If instead it's an object, it will be treated as a `releaseessentials.filter.Filter` object.

> Cell merging is not possible within this library

**Example using text**

    {
        "type": "table",
        "title": "My plain-text table",
        "content": {
            "style": "Grid Table 4 Accent 6",
            "columns": ["", ""],
            "rows": [
                ["Name", "Martin Proffitt"],
                ["Email", "mproffitt@jitsc.co.uk"]
            ]
    }

**Example using text and queries**

    {
        "type": "table",
        "content": {
            "title": "General statistics",
            "style": "Grid Table 4 Accent 6",
            "columns": [
                "",
                "value"
            ],
            "rows": [
                [
                    "Number of active projects",
                    {
                        "query": "project is not empty",
                        "collate": "total",
                        "fields": ["project"],
                        "distinct": "true"
                    }
                ],
                [
                    "Total number of open issues (including sub-tasks)",
                    {
                      "query": "status not in ('Done', 'Reject', 'Closed')",
                      "collate": "total",
                      "fields": ["key"]
                    }
                ],
                [
                    "Average age of open issues",
                    {
                        "query": "status not in ('Done', 'Reject', 'Closed')",
                        "collate": "average",
                        "field": "created"
                    }
                ],
                [
                    "Average duration of issues",
                    {
                        "query": "status in ('Done', 'Reject', 'Closed') and resolutiondate is not empty",
                        "collate": "average_duration",
                        "field": "resolutiondate"
                    }
                ]
            ]
        }
    }

**Example using queries**

    {
        "type": "table",
        "title": "Bugs",
        "content": {
            "style": "Light Shading Accent 6",
            "columns": [
                "JIRA Reference",
                "Description",
                "Business Representative"
            ],
            "rows": {
                "query": "fixVersion = '{FIX_VERSION}' and issuetype = Bug and 'Release text' is not empty and status= Done and resolution in (Done, Fixed)",
                "fields": [
                    "key",
                    "Release text",
                    "Business Representative"
                ]
            }
        }
    }


