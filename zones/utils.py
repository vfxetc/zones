
from ._compat import basestring


def is_fqdn(x):
	return x.endswith('.')


def join_name(*names):
    joined = ''
    for name in reversed(names):
        if is_fqdn(name) or not joined:
            joined = name
        else:
            joined = '{}.{}'.format(name, joined)
    return joined

