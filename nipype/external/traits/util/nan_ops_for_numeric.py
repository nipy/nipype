
# Since this module is meant to offer safety wrappers around some Numeric
# functions, if we can't import Numeric or scipy, then gracefully handle
# the import error and define stubs.

try:
    import Numeric as _nx
    from Numeric import asarray, reshape, argmin, argmax, compress
    from scipy.stats import mean, median
    from scipy import isnan, amin, amax, inf, isfinite


    def _asarray1d(arr):
        """Ensure 1d array for one array.
        """
        m = asarray(arr)
        if len(m.shape)==0:
            m = reshape(m,(1,))
        return m

    def nansum(x,axis=-1):
        """Sum the array over the given axis treating nans as missing values.
        """
        x = _asarray1d(x).copy()
        _nx.putmask(x,isnan(x),0)
        return _nx.sum(x,axis)

    def nanmin(x,axis=-1):
        """Find the minimium over the given axis ignoring nans.
        """
        x = _asarray1d(x).copy()
        _nx.putmask(x,isnan(x),inf)
        return amin(x,axis)

    def nanargmin(x,axis=-1):
        """Find the indices of the minimium over the given axis ignoring nans.
        """
        x = _asarray1d(x).copy()
        _nx.putmask(x,isnan(x),inf)
        return argmin(x,axis)


    def nanmax(x,axis=-1):
        """Find the maximum over the given axis ignoring nans.
        """
        x = _asarray1d(x).copy()
        _nx.putmask(x,isnan(x),-inf)
        return amax(x,axis)

    def nanargmax(x,axis=-1):
        """Find the maximum over the given axis ignoring nans.
        """
        x = _asarray1d(x).copy()
        _nx.putmask(x,isnan(x),-inf)
        return argmax(x,axis)

    def nanmean(x):
        """Find the mean of x ignoring nans.

            fixme: should be fixed to work along an axis.
        """
        x = _asarray1d(x).copy()
        y = compress(isfinite(x), x)
        return mean(y)

    def nanmedian(x):
        """Find the median over the given axis ignoring nans.

            fixme: should be fixed to work along an axis.
        """
        x = _asarray1d(x).copy()
        y = compress(isfinite(x), x)
        return median(y)

except ImportError:
    _asarray1d = nansum = nanmin = nanargmin = nanmax = nanargmax = \
            nanmean = nanmedian = None
