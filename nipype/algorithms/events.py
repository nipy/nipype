from __future__ import division
from builtins import range

from copy import deepcopy
import os

from nibabel import load
import numpy as np
from nipype.external.six import string_types
from nipype.interfaces.base import (BaseInterface, TraitedSpec, InputMultiPath,
                               traits, File, Bunch, BaseInterfaceInputSpec,
                               isdefined, OutputMultiPath)
from nipype import config, logging
import re
from glob import glob
from os.path import basename
iflogger = logging.getLogger('interface')

# Eventually, move the following inside the interface, or wrap in an import check
try:
    import pandas as pd
except ImportError:
    raise ImportError("The events module requires pandas.")


def alias(target, append=False):
    def decorator(func):
        def wrapper(self, cols, groupby=None, names=None, *args, **kwargs):

            cols = self._select_cols(cols)

            # groupby can be either a single column, in which case it's
            # interpreted as a categorical variable to groupby directly, or a
            # list of column names, in which case it's interpreted as a set of
            # dummy columns to reconstruct a categorical from.
            if groupby is not None:
                groupby = self._select_cols(groupby)
                if len(groupby) > 1:
                    group_results = []
                    names = ['%s_%s' % (cn, gn)for cn in cols for gn in groupby]
                    for i, col in enumerate(groupby):
                        _result = np.zeros((len(self.data), len(cols)))
                        inds = self.data[col].nonzero()
                        _result[inds] = target(self.data[cols].iloc[inds], *args, **kwargs)
                        group_results.extend(_result.T)
                    result = np.c_[group_results].squeeze().T
                    result = pd.DataFrame(result, columns=names)
                else:
                    result = self.data.groupby(groupby).apply(target, *args, **kwargs)
            else:
                result = target(self.data[cols], *args, **kwargs)

            if append:
                names = result.columns

            if names is not None:
                cols = names

            self.data[cols] = result
        return wrapper
    return decorator


class EventTransformer(object):

    def __init__(self, events, orig_hz=1, target_hz=1000):
        self.events = events
        self.orig_hz = orig_hz
        self.target_hz = target_hz
        self._to_dense()

    def _select_cols(self, cols):
        if isinstance(cols, string_types) and '*' in cols:
            # if '*' in cols:
            patt = re.compile(cols.replace('*', '.*'))
            cols = [l for l in self.data.columns.tolist() for m in [patt.search(l)] if m]
        return cols

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

    def _standardize(self, cols, demean=True, rescale=True, copy=True):
        cols = self._select_cols(cols)
        X = self.data[cols]
        self.data[cols] = (X - X.mean()) / np.std(X, 0)

    @alias(_standardize)
    def standardize(): pass

    def _binarize(self, cols, threshold=0.0):
        cols = self._select_cols(cols)
        X = self.data[cols].values
        above = X > threshold
        X[above] = 1
        X[~above] = 0
        self.data[cols] = X

    @alias(_binarize)
    def binarize(): pass

    def orthogonalize(self, y_cols, X_cols):
        ''' Orthogonalize each of the variables in y_cols with respect to all
        of the variables in x_cols.
        '''
        y_cols, X_cols = self._select_cols(y_cols), self._select_cols(X_cols)
        X = self.data[X_cols].values
        y = self.data[y_cols].values
        _aX = np.c_[np.ones(len(y)), X]
        coefs, resids, rank, s = np.linalg.lstsq(_aX, y)
        self.data[y_cols] = y - X.dot(coefs[1:])

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

    def multiply(self, y_cols, x_cols):
        x_cols = self._select_cols(x_cols)
        result = self.data[x_cols].apply(lambda x: np.multiply(x, self.data[y_cols]))
        names = ['%s_%s' % (y_cols, x) for x in x_cols]
        self.data[names] = result

    def query(self, q, *args, **kwargs):
        self.data = self.data.query(filter)

    def apply(self, func, *args, **kwargs):
        self.data = func(self.data, *args, **kwargs)

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
            columns (list): Optional list of column names to use. If passed,
                number of elements must match number of columns in the text
                files to be read. If omitted, column names are inferred by
                pandas (depending on value of header).
            header (str): passed to pandas; see pd.read_table docs for details.
            sep (str): column separator; see pd.read_table docs for details.
            default_duration (float): Optional default duration to set for all
                events. Will be ignored if a column named 'duration' is found.
            default_amplitude (float): Optional default amplitude to set for
                all events. Will be ignored if an amplitude column is found.
            condition_pattern (str): regex with which to capture condition
                names from input text file filenames. Only the first captured
                group will be used.
            subject_pattern (str): regex with which to capture subject
                names from input text file filenames. Only the first captured
                group will be used.
            run_pattern (str): regex with which to capture run names from input
                text file filenames. Only the first captured group will be used.
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
                                       'corresponding to onsets, durations, amplitudes, and names'))
    input_units = traits.Enum('secs', 'scans', mandatory=True,
                              desc=("Units of event onsets and durations (secs or scans). Output "
                                    "units are always in secs"))
    time_repetition = traits.Float(mandatory=True,
                                   desc=("Time between the start of one volume to the start of "
                                         "the next image volume."))
    # transformations = InputMultiPath(traits.List(File(exists=True)), mandatory=True,
    #                                  desc=("JSON specification of the transformations to perform."))


class SpecifyEventsOutputSpec(TraitedSpec):
    subject_info = OutputMultiPath(Bunch, mandatory=True,
                                  desc=("Bunch or List(Bunch) subject specific condition information. "
                                        "see :ref:`SpecifyModel` or SpecifyModel.__doc__ for details"))


class Transformation(object):

    def __init__(self, transformer, inputs, steps, outputs=None):

        self.transformer = transformer
        self.inputs = inputs
        self.steps = steps
        self.outputs = outputs
        self._validate()

    def _validate(self):
        missing = set(transform['input'] - set(self.transformer.data.columns))
        if missing:
            raise ValueError("Invalid column(s): %s" % missing)

    def run(self):
        pass


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

        # Transformation application logic goes here later
        # ...
        self.transformer.resample(self.inputs.time_repetition)

    def _run_interface(self, runtime):
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

