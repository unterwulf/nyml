import copy

from .exceptions import *
from .schema import make_schema

def loads(s, schema=None, text_key=None):
    lines = s.splitlines(keepends=True)
    return load(lines, schema, text_key)

def load(fp, schema=None, text_key=None):
    def finish_element(new_indent, line):
        nonlocal indent, stack, element
        while new_indent < indent:
            if isinstance(stack[-1][1], list):
                stack[-1][1].append(element)
            elif isinstance(stack[-1][1], str):
                if new_indent == stack[-1][0] and line and line[0] in '-+' \
                        and element is None:
                    indent = new_indent
                    return
                _, key = stack.pop()
                stack[-1][1][key] = element
            indent, element = stack.pop()

        if isinstance(element, list) and (not line or line[0] not in '-+') and stack:
            if isinstance(stack[-1][1], list):
                stack[-1][1].append(element)
            elif isinstance(stack[-1][1], str):
                _, key = stack.pop()
                stack[-1][1][key] = element
            indent, element = stack.pop()

    def remove_marker(line):
        return line[2:] if line[1:2] == ' ' else line[1:]

    def parse_line(line):
        nonlocal indent, stack, element
        if isinstance(element, str):
            element += '\n' + line
        elif line and line[0] in '-+':
            if element is None:
                element = []
            elif not isinstance(element, list):
                raise ParseError('unexpected list')
            stack.append([indent, element])
            indent += 2
            if line[0] == '-':
                element = remove_marker(line)
            else:
                element = None
                parse_line(remove_marker(line))
        else:
            parts = line.split(':', 1)
            if len(parts) == 1:
                if element is None:
                    element = line
                else:
                    raise ParseError('unexpected string')
            else:
                if element is None:
                    element = {}
                elif not isinstance(element, dict):
                    raise ParseError('unexpected dict')

                key, value = parts
                if value and value[0] == ' ':
                    value = value[1:]
                if not value:
                    value = None

                stack.append([indent, element])
                stack.append([indent, key])
                indent += 2
                element = value

    indent = 0
    stack = []
    element = None

    for lineno, line in enumerate(fp, start=1):
        line = line.rstrip('\n')

        if not line:
            break

        next_indent = indent + 2
        no_indent_line = line.lstrip()
        line_indent = len(line) - len(no_indent_line)

        if line_indent > next_indent:
            no_indent_line = ' '*(line_indent - next_indent) + no_indent_line
            line_indent = next_indent
        elif line_indent > indent:
            no_indent_line = ' '*(line_indent - indent) + no_indent_line
            line_indent = indent

        finish_element(line_indent, no_indent_line)

        try:
            parse_line(no_indent_line)
        except ParseError as e:
            raise ParseError(f'{e} at line {lineno}: {line}')

    finish_element(0, '')

    if text_key is not None:
        element[text_key] = ''.join(fp)

    if schema is None:
        return element
    elif element is None:
        return schema.get_default()
    else:
        return schema.decode(element)

def dumps(data, schema=None, text_key=None):
    parts = []
    indent = 0

    def save_type(data, schema=None, collapse=False):
        if isinstance(data, dict):
            save_dict(data, schema, collapse)
        elif isinstance(data, list):
            save_list(data, schema, collapse)
        elif data is None:
            parts.append('\n')
        else:
            lines = str(data).split('\n')
            if lines:
                if collapse:
                    parts.append(lines[0])
                    parts.append('\n')
                prefix = ' '*indent
                for line in lines[1 if collapse else 0:]:
                    parts.append(prefix)
                    parts.append(line)
                    parts.append('\n')

    def save_dict(dct, schema, collapse):

        def save_dict_item(dct, key):
            nonlocal parts, indent
            strkey = str(key)
            if strkey.startswith(('-', '+', '>')) \
                    or strkey.find(':') != -1 \
                    or strkey.find('\n') != -1:
                raise KeyError

            item_schema = schema.get_item_schema(key) \
                    if schema is not None \
                    else None

            if isinstance(dct[key], dict):
                parts.append('\n')
                indent += 2
                save_type(dct[key], item_schema)
                indent -= 2
            elif isinstance(dct[key], list):
                parts.append('\n')
                save_type(dct[key], item_schema)
            elif dct[key] is None:
                parts.append('\n')
            else:
                indent += 2
                value = str(dct[key])
                collapse = True
                # First line needs to be doubled if it's empty. This will allow
                # parser to distinguish a string from a dict or list when it's
                # a dict item.
                if value and value[0] == '\n':
                    parts.append('\n')
                    collapse = False
                else:
                    parts.append(' ')
                save_type(value, item_schema, collapse)
                indent -= 2

        if schema is not None and schema.schemas:
            keys = [k for k in schema.schemas.keys() if k in dct.keys()]
            keys += [k for k in dct.keys() if k not in keys]
        else:
            keys = list(dct.keys())

        if keys:
            if collapse:
                parts.append(str(keys[0]) + ':')
                save_dict_item(dct, keys[0])
            for key in keys[1 if collapse else 0:]:
                parts.append(' '*indent + str(key) + ':')
                save_dict_item(dct, key)

    def save_list(lst, schema, collapse):
        item_schema = schema.get_item_schema() if schema is not None else None

        def save_list_item(item):
            nonlocal indent
            indent += 2
            save_type(item, item_schema, collapse=True)
            indent -= 2

        def marker(item):
            if isinstance(item, list) or isinstance(item, dict):
                return '+ '
            else:
                return '- '

        if lst:
            if collapse:
                parts.append(marker(lst[0]))
                save_list_item(lst[0])
            for item in lst[1 if collapse else 0:]:
                parts.append(' '*indent + marker(item))
                save_list_item(item)

    if data is not None and data != '':
        text = None
        if text_key is not None and isinstance(data, dict):
            text = data.pop(text_key, None)

        if schema is not None:
            data = schema.encode(data)

        save_type(data, schema, collapse=False)

        if text:
            parts.append('\n')
            parts.append(text.replace('\r\n', '\n'))

    return ''.join(parts)

def dump(obj, fp, schema=None, text_key=None):
    fp.write(dumps(obj, schema, text_key))
