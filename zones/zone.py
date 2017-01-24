import functools
import re
import time

from .record import Record
from .utils import isfqdn
from .spf import SPF

sn_epoch_start = 1483207200


class Zone(object):

	def __init__(self, origin, primary_nameserver=None, hostmaster_email=None,
		serial_number=None, slave_refresh=None, slave_retry=None,
		slave_expiry=None, ttl=None,
	):

		if not isfqdn(origin):
			raise ValueError('origin must be FQDN')
		self.origin = origin

		if primary_nameserver:
			if not isfqdn(primary_nameserver):
				raise ValueError('primary_nameserver must be FQDN')
			self.primary_nameserver = primary_nameserver
		else:
			self.primary_nameserver = 'ns1.' + origin

		if hostmaster_email:
			if not isfqdn(hostmaster_email):
				raise ValueError('hostmaster_email must be FQDN')
			self.hostmaster_email = hostmaster_email.replace('@', '.')
		else:
			self.hostmaster_email = 'hostmaster.' + origin

		self.serial_number = serial_number or str(int(time.time() - sn_epoch_start))

		self.slave_refresh = slave_refresh or '1d'
		self.slave_retry = slave_retry or '1h'
		self.slave_expiry = slave_expiry or '4w'
		self.ttl = ttl or '1h'

		self.records = []
		self.spf_records = {}

	def add(self, *args, **kwargs):
		rec = Record(*args, **kwargs)
		self.records.append(rec)
		return rec

	def __getattr__(self, name):
		if re.match(r'^[A-Z]+', name):
			return functools.partial(self.add, type=name)
		else:
			raise AttributeError(name)

	def comment(self, comment):
		self.records.append(comment)

	def spf(self, name='@'):
		rec = self.spf_records.get(name)
		if rec is None:
			rec = SPF(name)
			self.records.append(rec)
			self.spf_records[name] = rec
		return rec

	def dumps(self):
		return ''.join(self.iterdumps())

	def iterdumps(self):

		yield '$ORIGIN %s\n' % self.origin
		yield '$TTL %s\n' % self.ttl

		yield '''@ IN SOA {primary_nameserver} {hostmaster_email} (
			{serial_number} ;; Serial number.
			{slave_refresh} ;; Slave refresh.
			{slave_retry} ;; Slave retry.
			{slave_expiry} ;; Slave expiry.
			{ttl} ;; Default TTL.
)
'''.format(**self.__dict__)

		for rec in self.records:
			if isinstance(rec, basestring):
				for line in rec.splitlines():
					yield ';; %s\n' % line.rstrip()
			else:
				yield rec.dumps()

