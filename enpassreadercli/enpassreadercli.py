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
from enpassreaderlib.enpassreaderlibexceptions import EnpassDatabaseError
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


def get_arguments():
    """
    Gets us the cli arguments.

    Returns the args as parsed from the argsparser.
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
                        help='If set then the value returned for the entry is going to he the password.',
                        dest='totp',
                        action='store_false')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", "--get",
                       help="The name of the entry to get the password of.",
                       dest='entry',
                       action='store')
    group.add_argument("-e", "--enumerate",
                       help="List all the passwords in the database.",
                       action="store_true",
                       dest='list')
    group.add_argument("-s", "--search",
                       help="Interactively search for an entry in the database and return that password.",
                       action="store_true",
                       dest='search')
    group.add_argument("-f", "--fuzzy-search",
                       help="Interactively fuzzy search for an entry in the database and return that password.",
                       action="store_true",
                       dest='fuzzy')
    parser.set_defaults(totp=False)
    args = parser.parse_args()
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


def main():
    """
    Main method.

    This method holds what you want to execute when
    the script is run on command line.
    """
    args = get_arguments()
    setup_logging(args.log_level, args.logger_config)
    try:
        enpass = EnpassDB(args.path, args.password, args.key_file)

        class EnpassCompleter(Completer):
            """Completer for enpass on keypress for the interactive search."""

            def get_completions(self, document, complete_event):
                for match in [entry.title for entry in enpass.search_entries(document.text)]:
                    yield Completion(match, start_position=-len(document.text))
    except EnpassDatabaseError:
        LOGGER.error(('Could not read or decrypt the database. '
                      'Please validate that the path provided is a valid enpass database, '
                      'and that the provided password and optionally key file are correct.'))
        raise SystemExit(1) from None
    if args.list:
        for entry in enpass.entries:
            print(f'{entry.title}: '
                  f'{pyotp.TOTP(entry.totp_seed.replace(" ", "")).now() if args.totp else entry.password}')
        raise SystemExit(0)
    if args.entry:
        entry_title = args.entry
    elif args.search or args.fuzzy:
        try:
            entry_title = prompt('Title :',
                                 completer=EnpassCompleter() if args.search else FuzzyCompleter(EnpassCompleter()))
        except KeyboardInterrupt:
            raise SystemExit(0) from None
    entry = enpass.get_entry(entry_title)
    if not entry:
        LOGGER.error(f'No password entry found with title of "{entry_title}".')
        raise SystemExit(1) from None
    print(pyotp.TOTP(entry.totp_seed.replace(" ", "")).now() if args.totp else entry.password)
    raise SystemExit(0) from None


if __name__ == '__main__':
    main()
