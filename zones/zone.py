import functools
import re
import time

from . import utils
from .record import Record
from .spf import SPF

EPOCH_OFFSET = -1483207200


class Zone(object):

    def __init__(self, origin, primary_nameserver=None, hostmaster_email=None,
        serial_number=None, slave_refresh=None, slave_retry=None,
        slave_expiry=None, ttl=None, epoch_offset=EPOCH_OFFSET,
    ):

        if not utils.is_fqdn(origin):
            raise ValueError('origin must be FQDN')
        self.origin = origin

        if primary_nameserver:
            if not utils.is_fqdn(primary_nameserver):
                raise ValueError('primary_nameserver must be FQDN')
            self.primary_nameserver = primary_nameserver
        else:
            self.primary_nameserver = 'ns1.' + origin

        if hostmaster_email:
            if not utils.is_fqdn(hostmaster_email):
                raise ValueError('hostmaster_email must be FQDN')
            self.hostmaster_email = hostmaster_email.replace('@', '.')
        else:
            self.hostmaster_email = 'hostmaster.' + origin

        self.serial_number = serial_number or str(int(time.time() + epoch_offset))

        self.slave_refresh = slave_refresh or '1d'
        self.slave_retry = slave_retry or '1h'
        self.slave_expiry = slave_expiry or '4w'
        self.ttl = ttl or '1h'

        self.records = []
        self.spf_records = {}

        # For dumping inside and outside of zones.
        self.extra_conf = {'type': 'master'}
        self.outer_conf = {}

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
        self.records.append(''.join('; ' + line for line in comment.splitlines()))

    def spf(self, name='@', default=''):
        rec = self.spf_records.get(name)
        if rec is None:
            rec = SPF(name)
            self.records.append(rec)
            self.spf_records[name] = rec
        rec.default = rec.default or default
        return rec

    def add_update_key(self, name, secret, algorithm='hmac-md5', update_policy='self'):
        fqdn = utils.join_name(name, self.origin)
        self.outer_conf['key "{}"'.format(fqdn)] = {
            'secret': '"{}"'.format(secret),
            'algorithm': algorithm
        }
        if update_policy:
            self.extra_conf.setdefault('update-policy', []).append(
                'grant {} {} {}'.format(fqdn, update_policy, self.origin)
            )

    def dumps_conf(self, *args, **kwargs):
        return ''.join(self.iterdumps_conf(*args, **kwargs))

    def iterdumps_conf(self, **kwargs):
        for x in utils.iterdumps_conf(self.outer_conf):
            yield x
        conf = self.extra_conf.copy()
        conf.update(kwargs)
        for x in utils.iterdumps_conf({'zone "{}"'.format(self.origin): conf}):
            yield x


    def dumps_zone(self):
        return ''.join(self.iterdumps_zone())

    def iterdumps_zone(self):

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
                yield rec.rstrip() + '\n'
            else:
                yield rec.dumps()

