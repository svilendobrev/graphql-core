class _Undefined(object):
    """A representation of an Undefined value distinct from a None value"""

    def __bool__(self):
        # type: () -> bool
        return False

    __nonzero__ = __bool__

    def __repr__(self):
        # type: () -> str
        return "Undefined"


Undefined = _Undefined()


class _UndefinedDefaultValue(object):
    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __eq__(self, other):
        return isinstance(other, _UndefinedDefaultValue)

    def __copy__(self):
        return self

    def __repr__(self):
        return 'UndefinedDefaultValue'


UndefinedDefaultValue = _UndefinedDefaultValue()
