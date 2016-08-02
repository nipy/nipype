from __future__ import division

import numpy as np
from nipype.external.six import string_types
from nipype.interfaces.base import (BaseInterface, TraitedSpec, InputMultiPath,
                               traits, File, Bunch, BaseInterfaceInputSpec,
                               isdefined, OutputMultiPath)
from nipype import logging
import re
from glob import glob
from os.path import basename
import json
iflogger = logging.getLogger('interface')


have_pandas = True
try:
    import pandas as pd
except:
    have_nipy = False


class Transformations(object):

    @staticmethod
    def standardize(data, demean=True, rescale=True):
        if demean:
            data -= data.mean(0)
        if rescale:
            data /= data.std(0)
        return data

    @staticmethod
    def orthogonalize(data, other):
        ''' Orthogonalize each of the variables in cols with respect to all
        of the variables in x_cols.
        '''
        y = data.values
        X = other.values
        _aX = np.c_[np.ones(len(y)), X]
        coefs, resids, rank, s = np.linalg.lstsq(_aX, y)
        return  y - X.dot(coefs[1:])

    @staticmethod
    def binarize(data, threshold=0.0):
        above = data > threshold
        data[above] = 1
        data[~above] = 0
        return data


def alias(target, append=False):
    def decorator(func):
        def wrapper(self, cols, groupby=None, output=None, *args, **kwargs):

            cols = self._select_cols(cols)
            data = self.data[cols]

            if 'other' in kwargs:
                kwargs['other'] = self.data[kwargs['other']]

            # groupby can be either a single column, in which case it's
            # interpreted as a categorical variable to groupby directly, or a
            # list of column output, in which case it's interpreted as a set of
            # dummy columns to reconstruct a categorical from.
            if groupby is not None:
                groupby = self._select_cols(groupby)
                if len(groupby) > 1:
                    group_results = []
                    output = ['%s_%s' % (cn, gn)for cn in cols for gn in groupby]
                    for i, col in enumerate(groupby):
                        _result = target(data, *args, **kwargs)
                        group_results.extend(_result.T)
                    result = np.c_[group_results].squeeze().T
                    result = pd.DataFrame(result, columns=output)
                else:
                    result = self.data.groupby(groupby).apply(target, data, *args, **kwargs)
            else:
                result = target(data, *args, **kwargs)

            if append:
                output = result.columns

            if output is not None:
                result = pd.DataFrame(result, columns=output)
                self.data = self.data.join(result)
            else:
                self.data[cols] = result
        return wrapper
    return decorator


class EventTransformer(object):

    def __init__(self, events, orig_hz=1, target_hz=1000):
        self.events = events
        self.orig_hz = orig_hz
        self.target_hz = target_hz
        self._to_dense()

    ### Aliased functions ###
    @alias(np.log)
    def log(): pass

    @alias(np.logical_or)
    def or_(): pass

    @alias(np.logical_and)
    def and_(): pass

    @alias(np.logical_not)
    def not_(): pass

    @alias(pd.get_dummies, append=True)
    def factor(): pass

    @alias(Transformations.standardize)
    def standardize(): pass

    @alias(Transformations.binarize)
    def binarize(): pass

    @alias(Transformations.orthogonalize)
    def orthogonalize(): pass

    ### Standard instance methods ###
    def select(self, cols):
        # Always retain onsets
        if 'onset' not in cols:
            cols.insert(0, 'onset')
        self.data = self.data[self._select_cols(cols)]

    def formula(self, f, target=None, replace=False, *args, **kwargs):
        from patsy import dmatrix
        result = dmatrix(f, self.data, return_type='dataframe', *args, **kwargs)
        if target is not None:
            self.data[target] = result
        elif replace:
            self.data[result.columns] = result
        else:
            raise ValueError("Either a target column must be passed or replace"
                             " must be True.")

    def multiply(self, cols, x_cols):
        x_cols = self._select_cols(x_cols)
        result = self.data[x_cols].apply(lambda x: np.multiply(x, self.data[cols]))
        output = ['%s_%s' % (cols, x) for x in x_cols]
        self.data[output] = result

    def rename(self, cols, output):
        rename = dict(zip(cols, output))
        self.data = self.data.rename(columns=rename)

    def query(self, q, *args, **kwargs):
        self.data = self.data.query(filter)

    def apply(self, func, *args, **kwargs):
        if isinstance(func, string_types):
            func = getattr(self, func)
        func(*args, **kwargs)

    def _select_cols(self, cols):
        if isinstance(cols, string_types) and '*' in cols:
            patt = re.compile(cols.replace('*', '.*'))
            cols = [l for l in self.data.columns.tolist() for m in [patt.search(l)] if m]
        return cols

    def _to_dense(self):
        """ Convert the sparse [onset, duration, amplitude] representation
        typical of event files to a dense matrix where each row represents
        a fixed unit of time. """
        end = int((self.events['onset'] + self.events['duration']).max())

        targ_hz, orig_hz = self.target_hz, self.orig_hz
        len_ts = end * targ_hz
        conditions = self.events['condition'].unique().tolist()
        n_conditions = len(conditions)
        ts = np.zeros((len_ts, n_conditions))

        _events = self.events.copy().reset_index()
        _events[['onset', 'duration']] = _events[['onset', 'duration']] * targ_hz / orig_hz

        cond_index = [conditions.index(c) for c in _events['condition']]
        ev_end = np.round(_events['onset'] + _events['duration']).astype(int)
        onsets = np.round(_events['onset']).astype(int)

        for i, row in _events.iterrows():
            ts[onsets[i]:ev_end[i], cond_index[i]] = row['amplitude']

        self.data = pd.DataFrame(ts, columns=conditions)
        onsets = np.arange(len(ts)) / self.target_hz
        self.data.insert(0, 'onset', onsets)

    def resample(self, sampling_rate):
        """
        Resample the design matrix to the specified sampling rate. Primarily
        useful for downsampling to match the TR, so as to export the design as
        a n(TR) x n(conds) matrix.
        """
        sampling_rate = np.round(sampling_rate * 1000)
        self.data.index = pd.to_datetime(self.data['onset'], unit='s')
        self.data = self.data.resample('%dL' % sampling_rate).mean()
        self.data['onset'] = self.data.index.astype(np.int64) / int(1e9)
        self.data = self.data.reset_index(drop=True)


class EventReader(object):

    def __init__(self, columns=None, header='infer', sep=None,
                 default_duration=0., default_amplitude=1.,
                 condition_pattern=None, subject_pattern=None,
                 run_pattern=None):
        '''
        Args:
            columns (list): Optional list of column output to use. If passed,
                number of elements must match number of columns in the text
                files to be read. If omitted, column output are inferred by
                pandas (depending on value of header).
            header (str): passed to pandas; see pd.read_table docs for details.
            sep (str): column separator; see pd.read_table docs for details.
            default_duration (float): Optional default duration to set for all
                events. Will be ignored if a column named 'duration' is found.
            default_amplitude (float): Optional default amplitude to set for
                all events. Will be ignored if an amplitude column is found.
            condition_pattern (str): regex with which to capture condition
                output from input text file fileoutput. Only the first captured
                group will be used.
            subject_pattern (str): regex with which to capture subject
                output from input text file fileoutput. Only the first captured
                group will be used.
            run_pattern (str): regex with which to capture run output from input
                text file fileoutput. Only the first captured group will be used.
        '''

        self.columns = columns
        self.header = header
        self.sep = sep
        self.default_duration = default_duration
        self.default_amplitude = default_amplitude
        self.condition_pattern = condition_pattern
        self.subject_pattern = subject_pattern
        self.run_pattern = run_pattern

    def read(self, path, condition=None, subject=None, run=None, rename=None):

        dfs = []

        if isinstance(path, string_types):
            path = glob(path)

        for f in path:
            _data = pd.read_table(f, names=self.columns, header=self.header,
                                  sep=self.sep)

            if rename is not None:
                _data = _data.rename(rename)

            # Validate and set CODA columns
            cols = _data.columns

            if 'onset' not in cols:
                raise ValueError(
                    "DataFrame is missing mandatory 'onset' column.")

            if 'duration' not in cols:
                if self.default_duration is None:
                    raise ValueError(
                        'Event file "%s" is missing \'duration\''
                        ' column, and no default_duration was provided.' % f)
                else:
                    _data['duration'] = self.default_duration

            if 'amplitude' not in cols:
                _data['amplitude'] = self.default_amplitude

            if condition is not None:
                _data['condition'] = condition_name
            elif 'condition' not in cols:
                cp = self.condition_pattern
                if cp is None:
                    cp = '(.*)\.[a-zA-Z0-9]{3,4}'
                m = re.search(cp, basename(f))
                if m is None:
                    raise ValueError(
                        "No condition column found in event file, no "
                        "condition_name argument passed, and attempt to "
                        "automatically extract condition from filename failed."
                        " Please make sure a condition is specified.")
                _data['condition'] = m.group(1)

            if subject is not None:
                _data['subject'] = subject
            elif self.subject_pattern is not None:
                m = re.search(self.subject_pattern, f)
                if m is None:
                    raise ValueError(
                        "Subject pattern '%s' failed to match any part of "
                        "filename '%s'." % (self.subject_pattern, f))
                _data['subject'] = m.group(1)

            if run is not None:
                _data['run'] = run
            elif self.run_pattern is not None:
                m = re.search(self.run_pattern, f)
                if m is None:
                    raise ValueError(
                        "Run pattern '%s' failed to match any part of "
                        "filename '%s'." % (self.run_pattern, f))
                _data['run'] = m.group(1)

            dfs.append(_data)

        return pd.concat(dfs, axis=0)


class SpecifyEventsInputSpec(BaseInterfaceInputSpec):
    subject_info = InputMultiPath(Bunch, mandatory=True, xor=['subject_info',
                                                              'event_files'],
                                  desc=("Bunch or List(Bunch) subject specific condition information. "
                                        "see :ref:`SpecifyModel` or SpecifyModel.__doc__ for details"))
    event_files = InputMultiPath(traits.List(File(exists=True)), mandatory=True,
                                 xor=['subject_info', 'event_files'],
                                 desc=('list of event description files in 1, 2, 3, or 4 column format '
                                       'corresponding to onsets, durations, amplitudes, and output'))
    input_units = traits.Enum('secs', 'scans', mandatory=True,
                              desc=("Units of event onsets and durations (secs or scans). Output "
                                    "units are always in secs"))
    time_repetition = traits.Float(mandatory=True,
                                   desc=("Time between the start of one volume to the start of "
                                         "the next image volume."))
    transformations = traits.File(exists=True, mandatory=False,
                                     desc=("JSON specification of the transformations to perform."))


class SpecifyEventsOutputSpec(TraitedSpec):
    subject_info = OutputMultiPath(Bunch, mandatory=True,
                                  desc=("Bunch or List(Bunch) subject specific condition information. "
                                        "see :ref:`SpecifyModel` or SpecifyModel.__doc__ for details"))


class SpecifyEvents(BaseInterface):

    input_spec = SpecifyEventsInputSpec
    output_spec = SpecifyEventsOutputSpec

    def _get_event_data(self):
        if isdefined(self.inputs.subject_info):
            info = self.inputs.subject_info
            return pd.from_records(info)
        else:
            info = self.inputs.event_files
            reader = EventReader(columns=['onset', 'duration', 'amplitude'])
            return reader.read(info[0])

    def _transform_events(self):
        events = self._get_event_data()
        self.transformer = EventTransformer(events)
        if isdefined(self.inputs.transformations):
            tf = json.load(open(self.inputs.transformations))
            for t in tf['steps']:
                name = t.pop('name')
                cols = t.pop('input', None)
                self.transformer.apply(name, cols, **t)

        self.transformer.resample(self.inputs.time_repetition)

    def _run_interface(self, runtime):
        if not have_pandas:
            raise ImportError("The SpecifyEvents interface requires pandas. "
                              "Please make sure that pandas is installed.")
        self._transform_events()
        return runtime

    def _df_to_bunch(self):
        
        if not hasattr(self, 'transformer'):
            self._transform_events()

        _data = self.transformer.data

        info = Bunch(conditions=[], onsets=[], durations=[], amplitudes=[])
        cols = [c for c in _data.columns if c not in {'onset'}]
        onsets = _data['onset'].values.tolist()
        info.conditions = cols

        for col in _data.columns:
            info.onsets.append(onsets)
            info.durations.append(self.inputs.time_repetition)
            info.amplitudes.append(_data[col].values.tolist())

        return info

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['subject_info'] = self._df_to_bunch()
        return outputs

