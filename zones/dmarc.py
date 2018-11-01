from __future__ import print_function

from collections import MutableMapping, OrderedDict as odict

from ._compat import basestring
from .record import Record


class UriListField(object):

    def coerce(self, values):
        if isinstance(values, basestring):
            values = values.split(',')
        return list(values)

    def dumps(self, values):
        parts = []
        for value in values:
            if '@' in value and ':' not in value:
                value = 'mailto:' + value
            parts.append(value)
        return ','.join(parts)


class IntField(object):

    def coerce(self, value):
        return int(value)

    def dumps(self, value):
        return value


class EnumField(object):

    def __init__(self, values):
        self.values = set(values)

    def coerce(self, value):
        value = str(value)
        if value not in self.values:
            raise ValueError("{!r} is not in {!r}.".format(value, self.values))
        return value

    def dumps(self, value):
        return value


class DMARC(Record):

    _fields = dict(
        adkim=EnumField(['r', 's']),
        aspf=EnumField(['r', 's']),
        fo=EnumField(['0', '1', 'd', 's']),
        p=EnumField(['none', 'quarantine', 'reject']),
        pct=IntField(),
        rf=EnumField(['afrf']),
        ri=IntField(),
        rua=UriListField(),
        ruf=UriListField(),
        sp=EnumField(['none', 'quarantine', 'reject']),
        v=EnumField(['DMARC1']),
    )

    def __init__(self, name, **kwargs):
        super(DMARC, self).__init__(name, type='TXT')
        self.data = odict()
        for key, default in (
            ('v', 'DMARC1'),
            ('p', 'none'),
            ('pct', '100'),
            ('sp', 'none'),
            ('aspf', 'r'),
            ('po', None),
            ('ruf', None),
            ('rua', None),
        ):
            value = kwargs.pop(key, default)
            if value is not None:
                self[key] = value
        if kwargs:
            raise ValueError("Unknown kwargs {!r}.".format(kwargs))

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        field = self._fields.get(key)
        if field is None:
            raise ValueError("Unknown field {!r}.".format(key))
        value = field.coerce(value)
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def update(self, data=None, **kwargs):
        for source in (data, kwargs):
            if not source:
                continue
            for k, v in source.items():
                self[k] = v

    def dumps(self):

        parts = []
        for key, value in self.data.items():
            field = self._fields[key]
            value = field.dumps(value)
            parts.append('{}={}'.format(key, value))

        return super(DMARC, self).dumps(data=['; '.join(parts)])

