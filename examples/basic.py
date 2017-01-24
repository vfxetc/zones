import sys

import zones


z = zones.Zone('example.com.')


z.A('@', '1.2.3.4')

z.NS('@', 'ns1')
z.NS('@', 'ns2')
z.A('ns1', '1.2.3.4')
z.A('ns2', '5.6.7.8')

def google_apps(zone, name='@', **kwargs):
	zone.comment('Google Apps - mail')
	zone.MX(name, 1, 'ASPMX.L.GOOGLE.COM.')
	zone.MX(name, 5, 'ALT1.ASPMX.L.GOOGLE.COM.')
	zone.MX(name, 5, 'ALT2.ASPMX.L.GOOGLE.COM.')
	zone.MX(name, 10, 'ASPMX2.GOOGLEMAIL.COM.')
	zone.MX(name, 10, 'ASPMX3.GOOGLEMAIL.COM.')
	spf = zone.spf(name)
	spf.add('include', '_spf.google.com')
	spf.default = spf.default or '-'

google_apps(z)

print z.dumps()

