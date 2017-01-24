from .record import Record

class SPF(Record):

	def __init__(self, *args, **kwargs):
		kwargs['type'] = 'TXT'
		super(SPF, self).__init__(*args, **kwargs)
		self.data = list(self.data)
		self.default = ''

	def add(self, type, spec, qualifier=''):
		if type not in ('all', 'include', 'a', 'mx', 'ptr', 'ip4', 'ip6', 'exists'):
			raise ValueError('Bad SPF type.')
		if qualifier not in ('', '+', '-', '?', '~'):
			raise ValueError('Bad SPF qualifier.')
		self.data.append('%s%s:%s' % (qualifier, type, spec))

	def dumps(self):

		if not (self.data or self.default):
			return ''

		parts = ['v=spf1']
		parts.extend(self.data)
		if self.default:
			parts.append('%sall' % self.default)

		return super(SPF, self).dumps(data=[' '.join(parts)])

