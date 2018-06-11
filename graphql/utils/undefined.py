class _Undefined(object):
    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __repr__(self):
        return 'Undefined'


Undefined = _Undefined()


class _UndefinedDefaultValue(object):
    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __eq__(self, other):
        return isinstance(other, _UndefinedDefaultValue)

    def __repr__(self):
        return 'UndefinedDefaultValue'


UndefinedDefaultValue = _UndefinedDefaultValue()
