import re

from unittest import TestCase as _TestCase
from collections import OrderedDict as odict

from zones import *


def simplify_match(x):
    x = x.strip()
    x = re.sub(r'\n\s*', '\n', x)
    x = re.sub(r'[ \t]+', ' ', x)
    return x

class TestCase(_TestCase):

    def assertMatches(self, pattern, value, message=None, flags=0):

        simple_pattern = simplify_match(pattern)
        simple_value = simplify_match(value)

        if not re.match(simple_pattern, simple_value, flags=flags):
            self.fail(message or ('"""{}""" does not match pattern """{}"""'.format(value, pattern)))

