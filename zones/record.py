
class Record(object):

    def __init__(self, name, *data, **kwargs):
        self.name = name
        self.data = data
        self.ttl = kwargs.pop('ttl', None)
        self.class_ = kwargs.pop('class_', 'IN')
        self.type = kwargs.pop('type', None)

        split = kwargs.pop('split_long', False)
        if len(data) == 1 and split:
            self.data = [data[0][i:i+255] for i in xrange(0, len(data[0]), 255)]

    def __str__(self):
        return self.dumps().rstrip()

    def dumps(self, data=None):
        parts = [self.name, self.ttl, self.class_, self.type or 'XXX']
        parts.extend(data if data is not None else self.data)
        parts = [str(x) for x in parts if x is not None]
        parts = [('"%s"' % x if ' ' in x else x) for x in parts]
        return ' '.join(parts) + '\n'
