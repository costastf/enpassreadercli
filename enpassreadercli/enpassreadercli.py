#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: enpassreadercli.py
#
# Copyright 2021 Costas Tyfoxylos
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#

"""
Main code for enpassreadercli.

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import logging
import logging.config
import os
import json
import argparse
import coloredlogs
import pyotp
from enpassreaderlib import EnpassDB
from enpassreaderlib.enpassreaderlibexceptions import (EnpassDatabaseError,
                                                       EnpassDecryptionError,
                                                       EnpassKeyfileError)
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion, FuzzyCompleter

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = '''google'''
__date__ = '''27-03-2021'''
__copyright__ = '''Copyright 2021, Costas Tyfoxylos'''
__credits__ = ["Costas Tyfoxylos"]
__license__ = '''MIT'''
__maintainer__ = '''Costas Tyfoxylos'''
__email__ = '''<costas.tyf@gmail.com>'''
__status__ = '''Development'''  # "Prototype", "Development", "Production".

# This is the main prefix used for logging
LOGGER_BASENAME = '''enpassreadercli'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


class DefaultVariable(argparse.Action):
    """Creates an action that looks up a variable in the environment."""

    # based on https://stackoverflow.com/questions/24104827/
    # python-argparse-mutually-exclusive-required-group-with-a-required-option
    def __init__(self, variable, required=True, default=None, **kwargs):
        if not default and variable:
            if variable in os.environ:
                default = os.environ[variable]
        if required and default:
            required = False
        super().__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class EnpassCompleter(Completer):
    """Completer for enpass on keypress for the interactive search."""

    def __init__(self, enpass):
        self.enpass = enpass

    def get_completions(self, document, complete_event):
        for match in [entry.title for entry in self.enpass.search_entries(document.text)]:
            yield Completion(match, start_position=-len(document.text))


class FieldCompleter(Completer):
    """Completer for the field labels of an entry for the interactive search."""

    def __init__(self, labels):
        self.labels = list(dict.fromkeys(label for label in labels if label))

    def get_completions(self, document, complete_event):
        text = document.text.lower()
        for label in self.labels:
            if text in label.lower():
                yield Completion(label, start_position=-len(document.text))


def get_totp_code(seed):
    """
    Calculates the current totp code of a totp seed.

    Args:
        seed: The totp seed to calculate the code for.

    Returns:
        totp (str): The current totp code if a seed is provided else None.

    """
    if not seed:
        return None
    return pyotp.TOTP(seed.replace(' ', '')).now()


def get_totp(entry):
    """
    Calculates the current totp code of an entry.

    Args:
        entry: The entry to calculate the totp code for.

    Returns:
        totp (str): The current totp code if the entry has a totp seed else None.

    """
    return get_totp_code(entry.totp_seed)


def get_field(entry, name):
    """
    Retrieves the first field of an entry matching a label or type.

    Fields are matched case insensitively on their label first and on their type if no label matches,
    the same way enpassreaderlib matches them.

    Args:
        entry: The entry to retrieve the field from.
        name: The label or type of the field to retrieve.

    Returns:
        field (Field): The first matching field if match found else None.

    """
    name = name.lower()
    by_label = [field for field in entry.fields if (field.label or '').lower() == name]
    by_type = [field for field in entry.fields if (field.type or '').lower() == name]
    return next(iter(by_label or by_type), None)


def get_value(entry, field=None, totp=False):
    """
    Retrieves the requested value of an entry.

    Args:
        entry: The entry to retrieve the value from.
        field: The label or type of the field to retrieve, the password is retrieved if not provided.
            The current totp code is retrieved for a totp field instead of its seed.
        totp: If set the current totp code is retrieved.

    Returns:
        value (str): The requested value if the entry has it else None.

    """
    if totp:
        return get_totp(entry)
    if field is not None:
        match = get_field(entry, field)
        if not match:
            return None
        return get_totp_code(match.value) if (match.type or '').lower() == 'totp' else match.value
    return entry.password


def get_arguments(arguments=None):
    """
    Gets us the cli arguments.

    Args:
        arguments: The arguments to parse, the command line arguments are parsed if not provided.

    Returns:
        args (Namespace): The args as parsed from the argsparser.

    """
    # https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser(description='A cli to access enpass 6 encrypted databases and read, '
                                                 'list and search values.')
    parser.add_argument('--log-config',
                        '-l',
                        action='store',
                        dest='logger_config',
                        help='The location of the logging config json file',
                        default='')
    parser.add_argument('--log-level',
                        '-L',
                        help='Provide the log level. Defaults to info.',
                        dest='log_level',
                        action='store',
                        default='info',
                        choices=['debug',
                                 'info',
                                 'warning',
                                 'error',
                                 'critical'])
    parser.add_argument('-d', '--database-path',
                        help=('Specify the path to the enpass database. '
                              '(Can also be specified using "ENPASS_DB_PATH" environment variable)'),
                        dest='path',
                        action=DefaultVariable,
                        variable='ENPASS_DB_PATH',
                        required=True)
    parser.add_argument('-p', '--database-password',
                        help=('Specify the password to the enpass database. '
                              '(Can also be specified using "ENPASS_DB_PASSWORD" environment variable)'),
                        dest='password',
                        action=DefaultVariable,
                        variable='ENPASS_DB_PASSWORD',
                        required=True)
    parser.add_argument('-r', '--pbkdf2-rounds',
                        help='Specify the number of pbkdf2 rounds, defaults to 320000. ',
                        dest='pbkdf2_rounds',
                        type=int,
                        default=320_000)
    parser.add_argument('-k', '--database-key-file',
                        help=("Specify the path to the enpass database key file if used. "
                              "(Can also be specified using \"ENPASS_DB_KEY_FILE\" environment variable)"),
                        dest='key_file',
                        action=DefaultVariable,
                        variable='ENPASS_DB_KEY_FILE',
                        required=False,
                        default='')
    parser.add_argument('-t',
                        '--totp',
                        help='If set then the value returned for the entry is going to be the totp if seed is set.',
                        dest='totp',
                        action='store_true')
    parser.add_argument('-n',
                        '--no-totp',
                        help='If set then the value returned for the entry is going to be the password. (The default.)',
                        dest='totp',
                        action='store_false')
    parser.add_argument('-F',
                        '--field',
                        help=('The label of the field to return the value of instead of the password, '
                              'matched case insensitively, falling back to the field type if no label matches. '
                              'A totp field returns its current code. '
                              'In interactive search, if not set, the field is prompted for.'),
                        dest='field',
                        action='store',
                        default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", "--get",
                       help="The name of the entry to get the value of.",
                       dest='entry',
                       action='store')
    group.add_argument("-e", "--enumerate",
                       help="List the value of all the entries in the database that have it.",
                       action="store_true",
                       dest='list')
    group.add_argument("-s", "--search",
                       help="Interactively search for an entry in the database and return its value.",
                       action="store_true",
                       dest='search')
    group.add_argument("-f", "--fuzzy-search",
                       help="Interactively fuzzy search for an entry in the database and return its value.",
                       action="store_true",
                       dest='fuzzy')
    parser.set_defaults(totp=False)
    args = parser.parse_args(arguments)
    if args.field is not None and not args.field.strip():
        parser.error('argument -F/--field: expected a non empty label or type')
    if args.field and args.totp:
        parser.error('argument -F/--field: not allowed with argument -t/--totp')
    return args


def setup_logging(level, config_file=None):
    """
    Sets up the logging.

    Needs the args to get the log level supplied

    Args:
        level: At which level do we log
        config_file: Configuration to use

    """
    # This will configure the logging, if the user has set a config file.
    # If there's no config file, logging will default to stdout.
    if config_file:
        # Get the config for the logger. Of course this needs exception
        # catching in case the file is not there and everything. Proper IO
        # handling is not shown here.
        try:
            with open(config_file, encoding='utf-8') as conf_file:
                configuration = json.loads(conf_file.read())
                # Configure the logger
                logging.config.dictConfig(configuration)
        except ValueError:
            print(f'File "{config_file}" is not valid json, cannot continue.')
            raise SystemExit(1) from None
    else:
        coloredlogs.install(level=level.upper())


def interactive_prompt(message, completer, fuzzy):
    """
    Prompts the user interactively with autocompletion.

    Args:
        message: The message of the prompt.
        completer: The completer providing the autocompletion.
        fuzzy: If set the autocompletion is fuzzy.

    Returns:
        text (str): The text the user provided.

    """
    try:
        return prompt(message, completer=FuzzyCompleter(completer) if fuzzy else completer)
    except (KeyboardInterrupt, EOFError):
        raise SystemExit(0) from None


def get_missing_value_message(entry, field=None, totp=False):
    """
    Composes the error message for an entry missing the requested value.

    Args:
        entry: The entry missing the value.
        field: The label or type of the requested field if any.
        totp: If set the totp code was requested.

    Returns:
        message (str): The error message.

    """
    if totp:
        return f'Entry with title of "{entry.title}" does not have a totp seed set.'
    if field:
        if get_field(entry, field):
            return f'Field with label or type of "{field}" in entry with title of "{entry.title}" has no value set.'
        labels = ', '.join(f'"{label}"' for label in FieldCompleter(entry.field_labels).labels) or 'none'
        return f'No field found with label or type of "{field}" in entry with title of "{entry.title}". ' \
               f'Available field labels are: {labels}.'
    return f'Entry with title of "{entry.title}" does not have a password set.'


def open_database(args):
    """
    Opens the enpass database.

    Args:
        args: The parsed cli arguments.

    Returns:
        enpass (EnpassDB): The opened database, exits with an error if it cannot be opened.

    """
    if not os.path.isfile(args.path):
        LOGGER.error(f'The database file "{args.path}" does not exist.')
        raise SystemExit(1)
    try:
        return EnpassDB(args.path, args.password, args.key_file, args.pbkdf2_rounds)
    except EnpassKeyfileError:
        LOGGER.error(f'The key file "{args.key_file}" does not hold a valid enpass key.')
        raise SystemExit(1) from None
    except EnpassDatabaseError:
        LOGGER.error(('Could not read or decrypt the database. '
                      'Please validate that the path provided is a valid enpass database, '
                      'that the provided password and optional key file are correct and that the pbkdf2 rounds'
                      f' provided ("{args.pbkdf2_rounds}") match the configuration of your database.'))
        raise SystemExit(1) from None


def list_values(enpass, field=None, totp=False):
    """
    Prints the requested value of all the entries that have it.

    Entries whose value fails authentication are reported and skipped.

    Args:
        enpass: The opened database.
        field: The label or type of the field to list, the password is listed if not provided.
        totp: If set the current totp code is listed.

    Returns:
        exit_code (int): 0 if all values could be decrypted else 1.

    """
    exit_code = 0
    for entry in enpass.entries:
        try:
            value = get_value(entry, field, totp)
        except EnpassDecryptionError:
            LOGGER.error(f'The value of entry with title of "{entry.title}" failed authentication, skipping.')
            exit_code = 1
            continue
        if value is not None:
            print(f'{entry.title}: {value}')
    return exit_code


def run(args, enpass):
    """
    Executes the requested action against the opened database.

    Args:
        args: The parsed cli arguments.
        enpass: The opened database.

    Returns:
        exit_code (int): The exit code of the cli.

    """
    if args.list:
        return list_values(enpass, args.field, args.totp)
    interactive = args.search or args.fuzzy
    entry_title = interactive_prompt('Title :', EnpassCompleter(enpass), args.fuzzy) if interactive else args.entry
    entry = enpass.get_entry(entry_title)
    if not entry:
        LOGGER.error(f'No entry found with title of "{entry_title}".')
        return 1
    field = args.field
    if interactive and not field and not args.totp:
        field = interactive_prompt('Field :', FieldCompleter(entry.field_labels), args.fuzzy)
        field = field if field.strip() else None
    try:
        value = get_value(entry, field, args.totp)
    except EnpassDecryptionError:
        LOGGER.error(f'The value of entry with title of "{entry.title}" failed authentication and cannot be trusted.')
        return 1
    if value is None:
        LOGGER.error(get_missing_value_message(entry, field, args.totp))
        return 1
    print(value)
    return 0


def main():
    """
    Main method.

    This method holds what you want to execute when
    the script is run on command line.
    """
    args = get_arguments()
    setup_logging(args.log_level, args.logger_config)
    with open_database(args) as enpass:
        exit_code = run(args, enpass)
    raise SystemExit(exit_code)


if __name__ == '__main__':
    main()
