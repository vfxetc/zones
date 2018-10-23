from . import *


class TestZone(TestCase):

    def test_basic_example(self):

        zone = Zone('example.com.')

        zone.A('foo', '1.2.3.4')
        zone.CNAME('bar', 'foo')
        zone.TXT('baz', 'text goes here')

        self.assertMatches(r'''

\$ORIGIN example.com.
\$TTL 1h
@ IN SOA ns1.example.com. hostmaster.example.com. \(
            \d+ ; Serial number.
            1d ; Secondary refresh.
            1h ; Secondary retry.
            4w ; Secondary expiry.
            1h ; Default TTL.
\)
foo IN A 1.2.3.4
bar IN CNAME foo
baz IN TXT "text goes here"

''', zone.dumps_zone())

