#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: test_enpassreadercli.py
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
test_enpassreadercli
----------------------------------
Tests for `enpassreadercli` module.

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import unittest as std_unittest

from betamax.fixtures import unittest
from enpassreaderlib.enpassreaderlib import Entry
from prompt_toolkit.document import Document

from enpassreadercli.enpassreadercli import (FieldCompleter, get_arguments, get_missing_value_message, get_totp,
                                             get_value)

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = '''google'''
__date__ = '''27-03-2021'''
__copyright__ = '''Copyright 2021, Costas Tyfoxylos'''
__credits__ = ["Costas Tyfoxylos"]
__license__ = '''MIT'''
__maintainer__ = '''Costas Tyfoxylos'''
__email__ = '''<costas.tyf@gmail.com>'''
__status__ = '''Development'''  # "Prototype", "Development", "Production".


class TestEnpassreadercli(unittest.BetamaxTestCase):

    def setUp(self):
        """
        Test set up

        This is where you can setup things that you use throughout the tests. This method is called before every test.
        """
        pass

    def tearDown(self):
        """
        Test tear down

        This is where you should tear down what you've setup in setUp before. This method is called after every test.
        """
        pass


def build_entry(fields, totp_seed=None):
    """Builds an entry with non sensitive fields and no password."""
    row = {'key': bytes(44),
           'title': 'Service',
           'uuid': '00000000-0000-0000-0000-000000000000',
           'password_value': None,
           'password_value_hash': None,
           'totp_value': totp_seed,
           'totp_value_hash': None,
           'totp_value_sensitive': 0}
    field_rows = [{'label': label, 'type': type_, 'value': value, 'sensitive': 0}
                  for label, type_, value in fields]
    return Entry(row, field_rows)


class TestValues(std_unittest.TestCase):

    def setUp(self):
        self.entry = build_entry([('Username', 'username', 'admin'),
                                  ('API key', 'text', 'key-value'),
                                  ('Client secret', 'text', 'secret-value')])

    def test_field_by_label(self):
        self.assertEqual(get_value(self.entry, 'api KEY'), 'key-value')

    def test_field_by_type(self):
        self.assertEqual(get_value(self.entry, 'username'), 'admin')

    def test_missing_field(self):
        self.assertIsNone(get_value(self.entry, 'nope'))

    def test_password_without_password_field(self):
        self.assertIsNone(get_value(self.entry))

    def test_totp_without_seed(self):
        self.assertIsNone(get_totp(self.entry))
        self.assertIsNone(get_value(self.entry, totp=True))

    def test_totp_field_returns_code_not_seed(self):
        entry = build_entry([('One-time code', 'totp', 'JBSWY3DPEHPK3PXP')])
        for name in ('one-time code', 'totp'):
            code = get_value(entry, name)
            self.assertEqual(len(code), 6)
            self.assertTrue(code.isdigit())

    def test_missing_value_messages(self):
        entry = build_entry([('Notes', 'text', None)])
        self.assertIn('has no value set', get_missing_value_message(entry, 'notes'))
        self.assertIn('Available field labels are: "Notes".', get_missing_value_message(entry, 'nope'))
        self.assertIn('Available field labels are: none.', get_missing_value_message(build_entry([]), 'nope'))

    def test_totp_with_seed(self):
        entry = build_entry([], totp_seed='JBSW Y3DP EHPK 3PXP')
        code = get_totp(entry)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())


class TestFieldCompleter(std_unittest.TestCase):

    def test_labels_are_deduplicated_and_empty_dropped(self):
        completer = FieldCompleter(['Password', None, '', 'API key', 'Password'])
        self.assertEqual(completer.labels, ['Password', 'API key'])

    def test_completions_match_case_insensitively(self):
        completer = FieldCompleter(['Password', 'API key', 'Client secret'])
        completions = completer.get_completions(Document('KE'), None)
        self.assertEqual([completion.text for completion in completions], ['API key'])


class TestArguments(std_unittest.TestCase):

    def test_field(self):
        args = get_arguments(['-d', 'db', '-p', 'pass', '-g', 'Service', '-F', 'API key'])
        self.assertEqual(args.field, 'API key')

    def test_field_with_totp_is_rejected(self):
        with self.assertRaises(SystemExit):
            get_arguments(['-d', 'db', '-p', 'pass', '-g', 'Service', '-F', 'API key', '-t'])

    def test_empty_field_is_rejected(self):
        with self.assertRaises(SystemExit):
            get_arguments(['-d', 'db', '-p', 'pass', '-g', 'Service', '-F', ''])
