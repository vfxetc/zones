
class Record(object):

	def __init__(self, name, *data, **kwargs):
		self.name = name
		self.data = data
		self.ttl = kwargs.pop('ttl', None)
		self.class_ = kwargs.pop('class_', 'IN')
		self.type = kwargs.pop('type', None)

	def __str__(self):
		return self.dumps().rstrip()

	def dumps(self, data=None):
		parts = [self.name, self.ttl, self.class_, self.type or 'XXX']
		parts.extend(data if data is not None else self.data)
		parts = [str(x) for x in parts if x is not None]
		parts = [('"%s"' % x if ' ' in x else x) for x in parts]
		return ' '.join(parts) + '\n'
