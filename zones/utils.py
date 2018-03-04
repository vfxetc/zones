

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


def iterdumps_conf(conf, level=0):

    if not level and not isinstance(conf, dict):
        raise TypeError("Level 0 conf must be a dict.")

    if isinstance(conf, basestring):
        yield conf + ';\n'
        return

    if level:
        yield '{\n'
    
    indent = '    ' * level
    
    if isinstance(conf, dict):
        for key, value in conf.iteritems():
            yield indent + key + ' '
            for x in iterdumps_conf(value, level + 1):
                yield x
    else:
        for value in conf:
            yield indent + value + ';\n'

    if level:
        yield ('    ' * (level - 1)) + '};\n'


def dumps_conf(*args, **kwargs):
    return ''.join(iterdumps_conf(*args, **kwargs))
