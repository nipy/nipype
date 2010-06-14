# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
''' Battery runner classes and Report classes '''

class BatteryRunner(object):

    def __init__(self, checks):
        self._checks = checks

    def check_only(self, obj):
        reports = []
        for check in self._checks:
            reports.append(check(obj, False))
        return reports

    def check_fix(self, obj):
        reports = []
        for check in self._checks:
            report = check(obj, True)
            obj = report.obj
            reports.append(report)
        return obj, reports

    def __len__(self):
        return len(self._checks)

class Report(object):
    def __init__(self,
                 obj=None,
                 error=None,
                 level=0,
                 problem_msg='',
                 fix_msg=''):
        ''' Initialize report with values

        Parameters
        ----------
        obj : object
           object tested, possibly fixed.  Default is None
        error : None or Exception
           Error to raise if raising error for this check.  If None,
           no error can be raised for this check (it was probably
           normal).
	level : int
           level of problem.  From 0 (no problem) to 50 (severe
           problem).  If the report originates from a fix, then this
           is the level of the problem remaining after the fix.
           Defaul is 0
	problem_msg : string
           String describing problem detected. Default is ''
	fix_msg : string
           String describing any fix applied.  Default is ''.

	Examples
	--------
        >>> rep = Report()
        >>> rep.level
        0
        >>> rep = Report((), TypeError, 10)
        >>> rep.level
        10
	   
        '''
        self.obj = obj
        self.error = error
        self.level = level
        self.problem_msg = problem_msg
        self.fix_msg = fix_msg

    def __eq__(self, other):
        ''' Test for equality

        Parameters
        ----------
        other : object
           report-like object to test equality

        Examples
        --------
        >>> rep = Report(level=10)
        >>> rep2 = Report(level=10)
        >>> rep == rep2
        True
        >>> rep3 = Report(level=20)
        >>> rep == rep3
        False
        '''
        return (self.__dict__ == other.__dict__)

    def __ne__(self, other):
        ''' Test for equality

        Parameters
        ----------
        other : object
           report-like object to test equality

        See __eq__ docstring for examples
        '''
        return (self.__dict__ != other.__dict__)

    def __str__(self):
        ''' Printable string for object '''
        return self.__dict__.__str__()

    @property
    def message(self):
        if self.fix_msg:
            return '; '.join((self.problem_msg, self.fix_msg))
        return self.problem_msg

    def log_raise(self, logger, error_level=40):
        logger.log(self.level, self.message)
        if self.level and self.level >= error_level:
            if self.error:
                raise self.error(self.problem_msg)

    def write_raise(self, stream, error_level=40, log_level=30):
        if self.level >= log_level:
            stream.write('Level %s: %s\n' % (self.level, self.message))
        if self.level and self.level >= error_level:
            if self.error:
                raise self.error(self.problem_msg)
