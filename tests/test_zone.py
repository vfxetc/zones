from . import *


class TestZone(TestCase):

    def test_conf_basics(self):

        zone = Zone('example.com.')

        zone.add_update_key('fookey', 'foosecret')


        self.assertMatches(r'''

key "fookey" {
    secret "foosecret";
    algorithm hmac-md5;
};

zone "example.com." {
    type master;
    update-policy {
        grant fookey self example.com.;
    };
};

''', zone.dumps_conf())


    def test_zone_basics(self):

        zone = Zone('example.com.')


        zone.A('foo', '1.2.3.4')
        zone.CNAME('bar', 'foo')
        zone.TXT('baz', 'text goes here')

        spf = zone.spf()
        spf.add('a', '3.4.5.6')

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

@ IN TXT "v=spf1 a:3.4.5.6"

''', zone.dumps_zone())


    def test_subzone_basics(self):

        zone = Zone('example.com.')
        sub = zone.subzone('sub')
        self.assertEqual(sub.name, 'sub')

        zone.A('foo', '1.2.3.4')
        rr = sub.A('foo', '2.3.4.5')
        self.assertEqual(rr.dumps(), 'foo.sub IN A 2.3.4.5\n')

        zone.CNAME('bar', 'foo')
        rr = sub.CNAME('bar', 'foo')
        self.assertEqual(rr.dumps(), 'bar.sub IN CNAME foo.sub\n')

        zone.TXT('baz', 'parent')
        sub.TXT('baz', 'child')

        spf = sub.spf()
        spf.add('a', '3.4.5.6')

        subsub = sub.subzone('sub2')
        self.assertEqual(subsub.name, 'sub2.sub')
        subsub.A('@', '4.5.6.7')

        rr = subsub.A('foo', '5.6.7.8')
        self.assertEqual(rr.dumps(), 'foo.sub2.sub IN A 5.6.7.8\n')

        self.assertMatches(r'''

foo IN A 1.2.3.4
foo.sub IN A 2.3.4.5
bar IN CNAME foo
bar.sub IN CNAME foo.sub
baz IN TXT parent
baz.sub IN TXT child

sub IN TXT "v=spf1 a:3.4.5.6"

sub2.sub IN A 4.5.6.7
foo.sub2.sub IN A 5.6.7.8

''', ''.join(zone.iterdumps_zone_body()))



