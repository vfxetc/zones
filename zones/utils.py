import re

from ._compat import basestring


def is_fqdn(x):
	return x.endswith('.')


def join_name(*names):
    res = []
    for name in reversed(names):
        for part in reversed(name.split('.')):
            if part in ('', '@'):
                res = [part]
            else:
                res.append(part)
    return '.'.join(reversed(res))


def resolve_origin(path, origin='@'):
    
    if origin != '@':
        path = re.sub(r'(^|\.)@(\.|$)', r'\1{}\2'.format(origin), path)

    path = join_name(path)

    return re.sub(r'(\.@)+', '', path)
