
from . import *

from zones.conf import *


class TestConf(TestCase):

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
