'Non-standard higher-order functions'

def partial(f, *a, **k): # (2.5 provides this)
    # Don't mutate 'a' or 'k' since each call to 'g' shares them
    def g(*b, **l):
        m = k.copy()
        m.update(l)
        return f(*(a + b), **m)
    return g

def compose(*fs):
    ''' ``compose(f,g,...,h)(*args, **kw) == f(g(...(h(*args, **kw))))``

        >>> compose(len, str)(100)
        3
        >>> compose(len, str, len, str)(1234567890)
        2
        >>> compose()(1)
        1
        >>> map(compose(sum, range, len), ['foo', 'asdf', 'wibble'])
        [3, 6, 15]
    '''

    if len(fs) == 0:
        return lambda x: x

    binary_compose = lambda f,g: lambda *args, **kw: f(g(*args, **kw))
    return reduce(binary_compose, fs)
