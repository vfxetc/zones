from collections import MutableMapping, OrderedDict as odict

from .record import Record


class DMARC(Record):

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
                self.data[key] = value
        self.data.update(kwargs)

    def __getitem__(self, key):
        return self.data[key]
    def __setitem__(self, key, value):
        self.data[key] = value
    def get(self, key, default=None):
        return self.data.get(key, default)

    def dumps(self):

        parts = []
        for k, v in self.data.items():
            if isinstance(v, (list, tuple)):
                v = ','.join(v)
            parts.append('{}={}'.format(k, v))

        return super(DMARC, self).dumps(data=['; '.join(parts)])

