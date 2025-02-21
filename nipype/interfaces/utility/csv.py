# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""CSV Handling utilities"""
import csv
from ..base import traits, TraitedSpec, DynamicTraitedSpec, File, BaseInterface
from ..io import add_traits


class CSVReaderInputSpec(DynamicTraitedSpec, TraitedSpec):
    in_file = File(
        exists=True, mandatory=True, desc="Input comma-seperated value (CSV) file"
    )
    header = traits.Bool(
        False, usedefault=True, desc="True if the first line is a column header"
    )
    delimiter = traits.String(",", usedefault=True, desc="Delimiter to use.")


class CSVReader(BaseInterface):
    """
    Examples
    --------

    >>> reader = CSVReader()  # doctest: +SKIP
    >>> reader.inputs.in_file = 'noHeader.csv'  # doctest: +SKIP
    >>> out = reader.run()  # doctest: +SKIP
    >>> out.outputs.column_0 == ['foo', 'bar', 'baz']  # doctest: +SKIP
    True
    >>> out.outputs.column_1 == ['hello', 'world', 'goodbye']  # doctest: +SKIP
    True
    >>> out.outputs.column_2 == ['300.1', '5', '0.3']  # doctest: +SKIP
    True

    >>> reader = CSVReader()  # doctest: +SKIP
    >>> reader.inputs.in_file = 'header.csv'  # doctest: +SKIP
    >>> reader.inputs.header = True  # doctest: +SKIP
    >>> out = reader.run()  # doctest: +SKIP
    >>> out.outputs.files == ['foo', 'bar', 'baz']  # doctest: +SKIP
    True
    >>> out.outputs.labels == ['hello', 'world', 'goodbye']  # doctest: +SKIP
    True
    >>> out.outputs.erosion == ['300.1', '5', '0.3']  # doctest: +SKIP
    True

    """

    input_spec = CSVReaderInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True

    def _append_entry(self, outputs, entry):
        for key, value in zip(self._outfields, entry):
            outputs[key].append(value)
        return outputs

    def _get_outfields(self):
        with open(self.inputs.in_file) as fid:
            reader = csv.reader(fid, delimiter=self.inputs.delimiter)

            entry = next(reader)
            if self.inputs.header:
                self._outfields = tuple(entry)
            else:
                self._outfields = tuple("column_" + str(x) for x in range(len(entry)))
        return self._outfields

    def _run_interface(self, runtime):
        self._get_outfields()
        return runtime

    def _outputs(self):
        return self._add_output_traits(super()._outputs())

    def _add_output_traits(self, base):
        return add_traits(base, self._get_outfields())

    def _list_outputs(self):
        outputs = self.output_spec().get()
        isHeader = True
        for key in self._outfields:
            outputs[key] = []  # initialize outfields
        with open(self.inputs.in_file) as fid:
            reader = csv.reader(fid, delimiter=self.inputs.delimiter)
            for entry in reader:
                if self.inputs.header and isHeader:  # skip header line
                    isHeader = False
                    continue
                outputs = self._append_entry(outputs, entry)
        return outputs
