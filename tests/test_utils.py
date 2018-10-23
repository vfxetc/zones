
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

        self.assertEqual(join_name('foo', '@'), 'foo.@')
        self.assertEqual(join_name('foo', '@', 'bar', '@'), 'foo.@')
        self.assertEqual(join_name('foo.', '@'), 'foo.')

        # This is kind odd, tbh.
        # self.assertEqual(join_name('foo.@@', '@'), 'foo.@@')
        # self.assertEqual(join_name('foo', '@@', 'a.bar'), 'foo.bar')
        # self.assertEqual(join_name('foo.@@.bar'), 'foo')
        # self.assertEqual(join_name('foo.@@.bar.baz'), 'foo.baz')

    def test_resolve_origin(self):

        self.assertEqual(resolve_origin('@'), '@')
        self.assertEqual(resolve_origin('foo'), 'foo')
        self.assertEqual(resolve_origin('foo.@'), 'foo')

        self.assertEqual(resolve_origin('foo.@', 'bar'), 'foo.bar')
        self.assertEqual(resolve_origin('foo.@', 'bar.@'), 'foo.bar')

        # self.assertEqual(resolve_origin('foo.@@', 'baz.bar'), 'foo.bar')
