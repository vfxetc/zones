from .record import Record

class SPF(Record):

    def __init__(self, *args, **kwargs):
        self.default = kwargs.pop('default', None)
        kwargs['type'] = 'TXT'
        super(SPF, self).__init__(*args, **kwargs)
        self.data = list(self.data)

    def add(self, type, spec=None, action=''):
        if type not in ('all', 'include', 'a', 'mx', 'ptr', 'ip4', 'ip6', 'exists'):
            raise ValueError('Bad SPF type.')
        if action not in ('', '+', '-', '?', '~'):
            raise ValueError('Bad SPF action.')
        if spec:
            self.data.append('%s%s:%s' % (action, type, spec))
        else:
            self.data.append('%s%s' % (action, type))

    def dumps(self):

        if not (self.data or self.default):
            return ''

        parts = ['v=spf1']
        parts.extend(self.data)
        if self.default:
            parts.append('%sall' % self.default)

        return super(SPF, self).dumps(data=[' '.join(parts)])

