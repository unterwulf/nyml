class NymlError(Exception):
    pass

class ParseError(NymlError):
    pass

class SchemaError(NymlError):
    pass

class SchemaViolation(NymlError):
    pass
