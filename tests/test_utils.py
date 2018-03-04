
from . import *

from zones.utils import *


class TestUtils(TestCase):

    def test_is_fdqn(self):
        self.assertTrue(is_fqdn('foo.'))
        self.assertTrue(is_fqdn('foo.bar.'))
        self.assertFalse(is_fqdn('foo'))
        self.assertFalse(is_fqdn('foo.bar'))

    def test_join_name(self):
        self.assertEqual(join_name('foo', 'bar'), 'foo.bar')
        self.assertEqual(join_name('foo', 'bar.com'), 'foo.bar.com')
        self.assertEqual(join_name('foo', 'bar.com.'), 'foo.bar.com.')
        self.assertEqual(join_name('foo.', 'bar.com'), 'foo.')

    def test_dumps_conf(self):
        self.assertEqual(dumps_conf(odict([
            ('zone "foo.com."', odict([
                ('type', 'master'),
                ('file', '"/path/to/zone"'),
            ])),
        ])),
'''zone "foo.com." {
    type master;
    file "/path/to/zone";
};
''')

        self.assertEqual(dumps_conf(odict([
            ('zone "foo.com."', odict([
                ('type', 'master'),
                ('file', '"/path/to/zone"'),
                ('update-policy', [
                    'grant * self foo.com.',
                ])
            ])),
        ])),
'''zone "foo.com." {
    type master;
    file "/path/to/zone";
    update-policy {
        grant * self foo.com.;
    };
};
''')