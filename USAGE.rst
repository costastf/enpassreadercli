=====
Usage
=====


To develop on enpassreadercli:

.. code-block:: bash

    # The following commands require pipenv as a dependency

    # To lint the project
    _CI/scripts/lint.py

    # To execute the testing
    _CI/scripts/test.py

    # To create a graph of the package and dependency tree
    _CI/scripts/graph.py

    # To build a package of the project under the directory "dist/"
    _CI/scripts/build.py

    # To see the package version
    _CI/scripts/tag.py

    # To bump semantic versioning [--major|--minor|--patch]
    _CI/scripts/tag.py --major|--minor|--patch

    # To upload the project to a pypi repo if user and password are properly provided
    _CI/scripts/upload.py

    # To build the documentation of the project
    _CI/scripts/document.py


To use enpassreadercli from the console:

.. code-block:: bash

    # Environment variables supported for required default arguments are:
    #
    # ENPASS_DB_PATH for the database path
    # ENPASS_DB_PASSWORD for the database password
    # ENPASS_DB_KEY_FILE for the key file if used.
    #
    # if any of the above are set the arguments can be omitted from the cli.

    enpass-reader --help
    usage: enpass-reader [-h] [--log-config LOGGER_CONFIG]
                         [--log-level {debug,info,warning,error,critical}] -d
                         PATH -p PASSWORD [-r PBKDF2_ROUNDS] [-k KEY_FILE]
                         [-t] [-n] [-F FIELD] (-g ENTRY | -e | -s | -f)

    A cli to access enpass 6 encrypted databases and read, list and search values.

    options:
      -h, --help            show this help message and exit
      --log-config LOGGER_CONFIG, -l LOGGER_CONFIG
                            The location of the logging config json file
      --log-level {debug,info,warning,error,critical}, -L {debug,info,warning,error,critical}
                            Provide the log level. Defaults to info.
      -d PATH, --database-path PATH
                            Specify the path to the enpass database. (Can also be
                            specified using "ENPASS_DB_PATH" environment variable)
      -p PASSWORD, --database-password PASSWORD
                            Specify the password to the enpass database. (Can also
                            be specified using "ENPASS_DB_PASSWORD" environment
                            variable)
      -r PBKDF2_ROUNDS, --pbkdf2-rounds PBKDF2_ROUNDS
                            Specify the number of pbkdf2 rounds, defaults to
                            320000.
      -k KEY_FILE, --database-key-file KEY_FILE
                            Specify the path to the enpass database key file if
                            used. (Can also be specified using
                            "ENPASS_DB_KEY_FILE" environment variable)
      -t, --totp            If set then the value returned for the entry is going
                            to be the totp if seed is set.
      -n, --no-totp         If set then the value returned for the entry is going
                            to be the password. (The default.)
      -F FIELD, --field FIELD
                            The label of the field to return the value of instead
                            of the password, matched case insensitively, falling
                            back to the field type if no label matches. A totp
                            field returns its current code. In interactive search,
                            if not set, the field is prompted for.
      -g ENTRY, --get ENTRY
                            The name of the entry to get the value of.
      -e, --enumerate       List the value of all the entries in the database that
                            have it.
      -s, --search          Interactively search for an entry in the database and
                            return its value.
      -f, --fuzzy-search    Interactively fuzzy search for an entry in the
                            database and return its value.


    # Getting one password
    enpass-reader -d PATH_TO_DATABASE -p PASSWORD -g some-password-name
    > password-value

    # Enumerate all passwords
    enpass-reader -d PATH_TO_DATABASE -p PASSWORD -e
    > password1-name: password1-value
    > password2-name: password2-value
    > password3-name: password3-value
    > password4-name: password4-value

    # Search interactively for a password
    enpass-reader -d PATH_TO_DATABASE -p PASSWORD -s
    > Title : (interactive prompt with wildcard searching and autocompletion
    # after choosing an entry from the autocompleted list and pressing enter at the "Field :" prompt
    > password-value-for-search-entry

    # Search interactively with fuzzy search for a password
    enpass-reader -d PATH_TO_DATABASE -p PASSWORD -f
    > Title : (interactive prompt with fuzzy searching and autocompletion
    # after choosing an entry from the autocompleted list and pressing enter at the "Field :" prompt
    > password-value-for-search-entry

    # Getting a field of an entry by its label (or type), case insensitively
    enpass-reader -d PATH_TO_DATABASE -p PASSWORD -g some-entry-name -F "API key"
    > api-key-value

    # Enumerate a field of all the entries that have it
    enpass-reader -d PATH_TO_DATABASE -p PASSWORD -e -F username
    > entry1-name: username1-value
    > entry2-name: username2-value

    # Getting the current totp code of an entry
    enpass-reader -d PATH_TO_DATABASE -p PASSWORD -g some-entry-name -t
    > 123456

    # In interactive search, if neither -F nor -t is set, the field is prompted for after the entry is chosen
    enpass-reader -d PATH_TO_DATABASE -p PASSWORD -f
    > Title : (interactive prompt with fuzzy searching and autocompletion
    > Field : (interactive prompt with autocompletion of the field labels of the chosen entry,
    #          pressing enter without input returns the password)
    > field-value-for-search-entry
