import copy

from .exceptions import *

class NymlSchema:
    def __init__(self, definition):
        self.default = definition.get('default')

    def get_default(self):
        return self.default

    def decode(self, entry):
        pass

    def encode(self, entry):
        pass


class NymlStrSchema(NymlSchema):
    def __init__(self, definition):
        super().__init__(definition)

        if self.default is None:
            self.default = ''
        elif not isinstance(self.default, str):
            raise SchemaError('type mismatch in default value'
                    f' (expected string, got {type(self.default).__name__})')

    def decode(self, entry):
        return '' if entry is None else entry

    def encode(self, entry):
        return entry


class NymlIntSchema(NymlSchema):
    def __init__(self, definition):
        super().__init__(definition)

        if self.default is None:
            self.default = 0
        else:
            try:
                self.default = int(self.default)
            except:
                raise SchemaError('type mismatch in default value')

    def decode(self, entry):
        try:
            return int(entry)
        except:
            raise SchemaViolation(f'invalid integer value: {entry}')

    def encode(self, entry):
        return str(entry)


class NymlBoolSchema(NymlSchema):
    def __init__(self, definition):
        super().__init__(definition)

        if self.default is None:
            self.default = False
        elif isinstance(self.default, str):
            self.default = self.decode(self.default)
        else:
            raise SchemaError('type mismatch in default value'
                    f' (expected bool, got {type(self.default).__name__})')

    def decode(self, entry):
        return entry in ('yes', 'true', '1', 'on')

    def encode(self, entry):
        return 'yes' if entry else 'no'


class NymlListSchema(NymlSchema):
    def __init__(self, definition):
        super().__init__(definition)

        if 'schema' in definition:
            self.schema = make_schema(definition['schema'])
        else:
            self.schema = None

        if self.default is None:
            self.default = []
        elif not isinstance(self.default, list):
            raise SchemaError('type mismatch in default value'
                    f' (expected list, got {type(self.default).__name__})')

    def get_item_schema(self):
        return self.schema

    def get_default(self):
        return copy.deepcopy(self.default)

    def decode(self, entry):
        if entry is None:
            return []
        elif not isinstance(entry, list):
            raise SchemaViolation(f'wrong type of {entry}'
                    f' (expected list, got {type(entry).__name__})')
        elif self.schema is not None:
            # Common schema for all elements
            return [self.schema.decode(v) for v in entry]
        else:
            return entry

    def encode(self, entry):
        if self.schema is not None:
            return [self.schema.encode(v) for v in entry]
        return entry


class NymlDictSchema(NymlSchema):
    def __init__(self, definition):
        super().__init__(definition)

        self.schema = None
        self.schemas = {}

        if 'schema' in definition:
            self.schema = make_schema(definition['schema'])
        elif 'schemas' in definition:
            for key in definition['schemas']:
                self.schemas[key] = make_schema(definition['schemas'][key])

        if self.default is None:
            self.default = {}
        elif not isinstance(self.default, dict):
            raise SchemaError('type mismatch in default value'
                    f' (expected dict, got {type(self.default).__name__})')

    def get_item_schema(self, key):
        return self.schemas.get(key, self.schema)

    def get_default(self):
        return self.decode(copy.deepcopy(self.default))

    def decode(self, entry):
        if entry is None:
            entry = {}
        elif not isinstance(entry, dict):
            raise SchemaViolation(f'wrong type of {entry}'
                    f' (expected dict, got {type(entry).__name__})')

        keys = set(entry)

        # Per element schemas
        for key, subschema in self.schemas.items():
            if key not in entry:
                entry[key] = subschema.get_default()
            else:
                entry[key] = subschema.decode(entry[key])
                keys.remove(key)

        # Common schema for all other elements
        if self.schema is not None:
            for key in keys:
                entry[key] = self.schema.decode(entry[key])

        return entry

    def encode(self, entry):
        return self.encode_reduced(self.reduce(entry))

    def encode_reduced(self, entry):
        for key in entry:
            subschema = self.get_item_schema(key)
            if subschema is not None:
                if hasattr(subschema, 'encode_reduced'):
                    entry[key] = subschema.encode_reduced(entry[key])
                else:
                    entry[key] = subschema.encode(entry[key])
        return entry

    def reduce(self, entry):
        # We must not modify input data, so we create a
        # new dictionary here.
        new_dict = {}
        for key in entry:
            subschema = self.get_item_schema(key)
            if subschema is not None:
                if hasattr(subschema, 'reduce'):
                    reduced_value = subschema.reduce(entry[key])
                else:
                    reduced_value = entry[key]

                if reduced_value != subschema.default:
                    new_dict[key] = reduced_value
            else:
                new_dict[key] = entry[key]

        return new_dict


def make_schema(definition):
    if definition is None:
        definition = {}

    typename = definition.get('type', 'str')

    if typename == 'dict':
        return NymlDictSchema(definition)
    elif typename == 'list':
        return NymlListSchema(definition)
    elif typename == 'bool':
        return NymlBoolSchema(definition)
    elif typename == 'int':
        return NymlIntSchema(definition)
    elif typename == 'str':
        return NymlStrSchema(definition)
    else:
        raise SchemaError(f'invalid type {typename}')
