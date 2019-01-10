import functools
import re
import time

from . import utils
from . import conf
from ._compat import basestring
from .record import Record
from .spf import SPF
from .dmarc import DMARC


EPOCH_OFFSET = -1483207200




class Zone(object):

    def __init__(self, origin, primary_nameserver=None, hostmaster_email=None,
        serial_number=None, secondary_refresh=None, secondary_retry=None,
        secondary_expiry=None, ttl=None, epoch_offset=EPOCH_OFFSET,
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

        self.secondary_refresh = secondary_refresh or '1d'
        self.secondary_retry = secondary_retry or '1h'
        self.secondary_expiry = secondary_expiry or '4w'

        self.ttl = ttl or '1h'

        self.records = []
        self._structured_txt_records = {}

        # For dumping inside and outside of zones.
        self.extra_conf = {'type': 'master'}
        self.outer_conf = {}

    def subzone(self, name):
        return Subzone(self, name)

    def add(self, name, *args, **kwargs):
        rec = Record(name, *args, **kwargs)
        self.records.append(rec)
        return rec

    def __getattr__(self, name):
        if re.match(r'^[A-Z]+', name):
            return functools.partial(self.add, type=name)
        else:
            raise AttributeError(name)

    def _structured_txt(self, struct_type, name, cls):
        name = utils.resolve_origin(name)
        map_ = self._structured_txt_records.setdefault(struct_type, {})
        try:
            return map_[name]
        except KeyError:
            rec = map_[name] = cls(name)
            self.records.append(rec)
            return rec

    def comment(self, comment):
        self.records.append(''.join('; ' + line for line in comment.splitlines()))

    def dmarc(self, name='@', **kwargs):
        name = utils.join_name('_dmarc', name)
        rec = self._structured_txt('dmarc', name, DMARC)
        rec.update(kwargs)
        return rec

    def spf(self, name='@', default=''):
        rec = self._structured_txt('spf', name, SPF)
        rec.default = rec.default or default
        return rec

    def add_update_key(self, key_name, secret, algorithm='hmac-md5', match='self', target=None, permission='grant', type=None):

        fqdn = utils.resolve_origin(utils.join_name(key_name, '@'), self.origin)
        self.outer_conf['key "{}"'.format(fqdn)] = {
            'secret': '"{}"'.format(secret),
            'algorithm': algorithm
        }

        # Bind says "optional" tname should be the same as the identity.
        if target is None:
            if match in ('self', 'selfsub', 'selfwildcard'):
                target = key_name + '.' + self.origin

        if match:
            if permission not in ('grant', 'deny'):
                raise ValueError("Invalid permission.", permission)
            if match not in ('6to4-self', 'external', 'krb5-self', 'krb5-subdomain', 'ms-self',
                    'ms-subdomain', 'name', 'self', 'selfsub', 'selfwildcard', 'subdomain',
                    'tcp-self', 'wildcard', 'zonesub', '*'):
                raise ValueError("Invalid match type.", match)
            self.extra_conf.setdefault('update-policy', []).append(
                '{} {} {} {}'.format(permission, fqdn, match, target if target else '', type if type else '')
            )

    def dumps_conf(self, *args, **kwargs):
        return ''.join(self.iterdumps_conf(*args, **kwargs))

    def iterdumps_conf(self, **kwargs):
        for x in conf.iterdumps_conf(self.outer_conf):
            yield x
        extra_conf = self.extra_conf.copy()
        extra_conf.update(kwargs)
        for x in conf.iterdumps_conf({'zone "{}"'.format(self.origin): extra_conf}):
            yield x

    def dumps_zone(self):
        return ''.join(self.iterdumps_zone())

    def iterdumps_zone(self):
        for x in self.iterdumps_zone_head():
            yield x
        for x in self.iterdumps_zone_body():
            yield x

    def iterdumps_zone_head(self):

        yield '$ORIGIN %s\n' % self.origin
        yield '$TTL %s\n' % self.ttl

        yield '''@ IN SOA {primary_nameserver} {hostmaster_email} (
            {serial_number} ; Serial number.
            {secondary_refresh} ; Secondary refresh.
            {secondary_retry} ; Secondary retry.
            {secondary_expiry} ; Secondary expiry.
            {ttl} ; Default TTL.
)
'''.format(**self.__dict__)

    def iterdumps_zone_body(self):
        for rec in self.records:
            if isinstance(rec, basestring):
                yield rec.rstrip() + '\n'
            else:
                yield rec.dumps()


class Subzone(object):

    def __init__(self, root, name):
        self.root = root
        self.name = name
        self.origin = utils.join_name(name, root.origin)

    def subzone(self, name):
        return Subzone(self.root, utils.join_name(name, self.name))

    def resolve_name(self, name):
        return utils.resolve_origin(utils.join_name(name, '@'), self.name)

    def __getattr__(self, name):
        if re.match(r'^[A-Z]+', name):
            return functools.partial(self.add, type=name)
        else:
            raise AttributeError(name)

    def add(self, name, *args, **kwargs):
        return self.root.add(self.resolve_name(name), *args, **kwargs)

    def CNAME(self, name, other, *args, **kwargs):
        return self.root.add(self.resolve_name(name), self.resolve_name(other), *args, type='CNAME', **kwargs)

    def spf(self, name='@', *args, **kwargs):
        return self.root.spf(self.resolve_name(name), *args, **kwargs)




