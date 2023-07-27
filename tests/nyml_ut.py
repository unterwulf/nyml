#!/usr/bin/env python3
#
# NYML unittest
#
import os
import sys
import unittest

SRCDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.insert(0, SRCDIR)

import nyml


def read_file(filename):
    with open(filename, newline='') as f:
        return f.read()

def make_schema_from_string(string):
    return nyml.make_schema(nyml.loads(string))

def load_schema_from_file(filename):
    return make_schema_from_string(read_file(filename))


class NymlParserTests(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_none(self):
        self.assertEqual(None, nyml.loads(''))
        self.assertEqual('', nyml.dumps(None))

    def test_str_empty(self):
        self.assertEqual('', nyml.dumps(''))
        schema = make_schema_from_string('type: str')
        self.assertEqual('', nyml.loads('', schema))

    def test_str(self):
        s = 'string'
        self.assertEqual(s, nyml.loads(s))
        self.assertEqual(s + '\n', nyml.dumps(s))

    def test_str_multiline(self):
        data = ('line1\n'
                '+ line2\n'
                ' line3: colon\n'
                'line4')
        text = ('line1\n'
                '+ line2\n'
                ' line3: colon\n'
                'line4\n')
        self.assertEqual(text, nyml.dumps(data))
        self.assertEqual(data, nyml.loads(text))
        self.assertEqual(data, nyml.loads(data))

    def test_int_empty(self):
        schema = make_schema_from_string('type: int')
        self.assertEqual(0, nyml.loads('', schema))

    def test_int_default_empty(self):
        schema = make_schema_from_string('type: int\n'
                                         'default: 42')
        self.assertEqual(42, nyml.loads('', schema))

    def test_int(self):
        self.assertEqual('42\n', nyml.dumps(42))
        schema = make_schema_from_string('type: int')
        self.assertEqual(42, nyml.loads('42\n', schema))
        self.assertEqual(42, nyml.loads('42', schema))

    def test_int_schema_violation(self):
        schema = make_schema_from_string('type: int')
        with self.assertRaises(nyml.SchemaViolation) as cm:
            nyml.loads('one', schema)
        self.assertEqual(str(cm.exception), 'invalid integer value: one')

    def test_bool_empty(self):
        schema = make_schema_from_string('type: bool')
        self.assertEqual(False, nyml.loads('', schema))

    def test_bool_default_empty(self):
        schema = make_schema_from_string('type: bool\n'
                                         'default: yes')
        self.assertEqual(True, nyml.loads('', schema))

    def test_bool(self):
        schema = make_schema_from_string('type: bool')
        self.assertEqual('yes\n', nyml.dumps(True, schema))
        self.assertEqual('no\n', nyml.dumps(False, schema))
        self.assertEqual(True, nyml.loads('yes\n', schema))
        self.assertEqual(True, nyml.loads('yes', schema))
        self.assertEqual(True, nyml.loads('true', schema))
        self.assertEqual(True, nyml.loads('1', schema))
        self.assertEqual(False, nyml.loads('no', schema))
        self.assertEqual(False, nyml.loads('false', schema))
        self.assertEqual(False, nyml.loads('0', schema))

    def test_list_empty(self):
        self.assertEqual('', nyml.dumps([]))
        schema = make_schema_from_string('type: list')
        self.assertEqual([], nyml.loads('', schema))

    def test_list(self):
        data = [1, "str", None]
        text = ('- 1\n'
                '- str\n'
                '- \n')
        self.assertEqual(text, nyml.dumps(data))

    def test_list_multiline(self):
        data = ["line1", "line2\n line3\nline4", "line5"]
        text = ('- line1\n'
                '- line2\n'
                '   line3\n'
                '  line4\n'
                '- line5\n')
        self.assertEqual(text, nyml.dumps(data))
        self.assertEqual(data, nyml.loads(text))

    def test_list_malformed(self):
        msgs = ['unexpected string at line 3: line3',
                'unexpected dict at line 2: line2: value2',
                'unexpected list at line 2:   - value2',
                'unexpected string at line 2:   value2']
        texts = [('- line1\n'
                  '- line2\n'
                  'line3\n'),
                 ('- line1\n'
                  'line2: value2\n'),
                 ('+ key1: value1\n'
                  '  - value2\n'),
                 ('+ key1: value1\n'
                  '  value2\n')]
        for text, msg in zip(texts, msgs):
            with self.assertRaises(nyml.ParseError) as cm:
                nyml.loads(text)
            self.assertEqual(str(cm.exception), msg)

    def test_list_schema_violation(self):
        schema = make_schema_from_string('type: list')
        with self.assertRaises(nyml.SchemaViolation) as cm:
            nyml.loads('value', schema)
        self.assertEqual(str(cm.exception), 'wrong type of value'
                                            ' (expected list, got str)')

    def test_list_of_ints(self):
        schema = make_schema_from_string('type: list\n'
                                         'schema:\n'
                                         '  type: int\n')
        data = [ 1, 3, 5, 7, 11 ]
        text = ('- 1\n'
                '- 3\n'
                '- 5\n'
                '- 7\n'
                '- 11\n')
        self.assertEqual(text, nyml.dumps(data, schema))
        self.assertEqual(data, nyml.loads(text, schema))

    def test_list_of_ints_schema_violation(self):
        schema = make_schema_from_string('type: list\n'
                                         'schema:\n'
                                         '  type: int\n')
        text = ('- 1\n'
                '- \n'
                '- 5\n')
        with self.assertRaises(nyml.SchemaViolation) as cm:
            nyml.loads(text, schema)
        self.assertEqual(str(cm.exception), 'invalid integer value: ')

    def test_list_of_lists(self):
        data = [['a', 'b'], [['c', 'd'], 'e']]
        text = ('+ - a\n'
                '  - b\n'
                '+ + - c\n'
                '    - d\n'
                '  - e\n')
        self.assertEqual(text, nyml.dumps(data))
        self.assertEqual(data, nyml.loads(text))

    def test_list_of_dicts(self):
        data = [{ 'a': '1', 'b': '2' }, { 'c': '3', 'd': '4' }]
        text = ('+ a: 1\n'
                '  b: 2\n'
                '+ c: 3\n'
                '  d: 4\n')
        self.assertEqual(text, nyml.dumps(data))
        self.assertEqual(data, nyml.loads(text))

    def test_dict_empty(self):
        self.assertEqual('', nyml.dumps({}))
        schema = make_schema_from_string('type: dict')
        self.assertEqual({}, nyml.loads('', schema))

    def test_dict_implicit_default(self):
        schema = make_schema_from_string(
            'type: dict\n'
            'schemas:\n'
            '  bool_key:\n'
            '    type: bool\n'
            '  int_key:\n'
            '    type: int\n'
            '  list_key:\n'
            '    type: list\n'
            '  dict_key:\n'
            '    type: dict\n'
            '  key:\n')
        data = { 'bool_key': False,
                 'int_key':  0,
                 'list_key': [],
                 'dict_key': {},
                 'key':      '' }
        self.assertEqual(data, nyml.loads('', schema))
        self.assertEqual('', nyml.dumps(data, schema))

    def test_dict_explicit_default(self):
        schema = make_schema_from_string(
            'type: dict\n'
            'schemas:\n'
            '  bool_key_true_by_default:\n'
            '    type: bool\n'
            '    default: yes\n'
            '  bool_key_false_by_default:\n'
            '    type: bool\n'
            '    default: no\n'
            '  int_key:\n'
            '    type: int\n'
            '    default: 42\n'
            '  list_key:\n'
            '    type: list\n'
            '    default:\n'
            '      - item1\n'
            '      - item2\n'
            '  dict_key:\n'
            '    type: dict\n'
            '    default:\n'
            '      key: value\n'
            '  key:\n'
            '    default: value\n')
        data = { 'bool_key_true_by_default': True,
                 'bool_key_false_by_default': False,
                 'int_key':  42,
                 'list_key': [ 'item1', 'item2' ],
                 'dict_key': { 'key': 'value' },
                 'key': 'value' }
        self.assertEqual(data, nyml.loads('', schema))
        self.assertEqual('', nyml.dumps(data, schema))

    def test_dict_homogeneous_default(self):
        schema = make_schema_from_string(
            'type: dict\n'
            'schemas:\n'
            '  page_dirs:\n'
            '    type: dict\n'
            '    schema:\n'
            '      type: str\n'
            '    default:\n'
            '      text/html: pages\n')
        data = { 'page_dirs': { 'text/html': 'pages' } }
        self.assertEqual(data, nyml.loads('', schema))
        self.assertEqual('', nyml.dumps(data, schema))

        data2 = { 'page_dirs': {} }
        self.assertEqual(data2, nyml.loads('page_dirs:', schema))
        self.assertEqual('page_dirs:\n', nyml.dumps(data2, schema))

    def test_dict_nested_default(self):
        schema = make_schema_from_string(
            'type: dict\n'
            'schemas:\n'
            '  vars:\n'
            '    type: dict\n'
            '    schemas:\n'
            '      bool_key_true_by_default:\n'
            '        type: bool\n'
            '        default: yes\n'
            '      bool_key_false_by_default:\n'
            '        type: bool\n'
            '        default: no\n'
            '      int_key:\n'
            '        type: int\n'
            '        default: 42\n'
            '      list_key:\n'
            '        type: list\n'
            '        default:\n'
            '          - item1\n'
            '          - item2\n'
            '      dict_key:\n'
            '        type: dict\n'
            '        default:\n'
            '          key: value\n'
            '      key:\n'
            '        default: value\n')

        data = { 'vars': { 'bool_key_true_by_default': True,
                           'bool_key_false_by_default': False,
                           'int_key':  42,
                           'list_key': [ 'item1', 'item2' ],
                           'dict_key': { 'key': 'value' },
                           'key':      'value' } }
        self.assertEqual(data, nyml.loads('', schema))
        self.assertEqual(data, nyml.loads('vars:', schema))
        self.assertEqual('', nyml.dumps(data, schema))

    def test_dict(self):
        data = { 'a': 'str', 'b': '\n', 'c': '\nstr', 'd': None }
        text = ('a: str\n'
                'b:\n'
                '  \n'
                '  \n'
                'c:\n'
                '  \n'
                '  str\n'
                'd:\n')
        self.assertEqual(text, nyml.dumps(data))
        self.assertEqual(data, nyml.loads(text))

    def test_dict_malformed(self):
        msgs = ['unexpected string at line 3: c',
                'unexpected list at line 3: - c',
                'unexpected list at line 3: + c']
        texts = [('a: 1\n'
                  'b: str\n'
                  'c\n'),
                 ('a: 1\n'
                  'b: str\n'
                  '- c\n'),
                 ('a: 1\n'
                  'b: str\n'
                  '+ c\n')]
        for text, msg in zip(texts, msgs):
            with self.assertRaises(nyml.ParseError) as cm:
                nyml.loads(text)
            self.assertEqual(msg, str(cm.exception))

    def test_dict_schema_violation(self):
        schema = make_schema_from_string('type: dict')
        with self.assertRaises(nyml.SchemaViolation) as cm:
            nyml.loads('value', schema)
        self.assertEqual(str(cm.exception), 'wrong type of value'
                                            ' (expected dict, got str)')

    def test_dict_of_int_schema_violation(self):
        schema = make_schema_from_string('type: dict\n'
                                         'schema:\n'
                                         '  type: int\n')
        text = ('a: 1\n'
                'b:\n'
                'c: 3\n')

        with self.assertRaises(nyml.SchemaViolation) as cm:
            nyml.loads(text, schema)
        self.assertEqual(str(cm.exception), 'invalid integer value: None')

    def test_dict_of_lists(self):
        data = { 'a': [1, 2], 'b': [3, 4] }
        text = ('a:\n'
                '- 1\n'
                '- 2\n'
                'b:\n'
                '- 3\n'
                '- 4\n')
        self.assertEqual(text, nyml.dumps(data))


if __name__ == '__main__':
    unittest.main()
