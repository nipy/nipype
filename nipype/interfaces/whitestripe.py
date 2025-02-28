from nipype.interfaces.r import RCommand
from nipype.interfaces.base import (
    TraitedSpec,
    BaseInterface,
    BaseInterfaceInputSpec,
    File,
    traits,
)
import os
import tempfile
from string import Template


class WhiteStripeInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True)
    out_file = File("out.nii.gz", usedefault=True)
    indices = traits.Array(desc="WhiteStripe indices", mandatory=False)
    img_type = traits.String(
        desc="WhiteStripe image type", mandatory=False, default="T1"
    )


class WhiteStripeOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class WhiteStripe(BaseInterface):
    input_spec = WhiteStripeInputSpec
    output_spec = WhiteStripeOutputSpec

    def _run_interface(self, runtime):
        tmpfile, script = self._cmdline(runtime)

        # rfile = True  will create a .R file with your script and executed.
        # Alternatively
        # rfile can be set to False which will cause the R code to be
        # passed
        # as a commandline argument to the R executable
        # (without creating any files).
        # This, however, is less reliable and harder to debug
        # (code will be reduced to
        # a single line and stripped of any comments).
        rcmd = RCommand(script=script, rfile=False)
        result = rcmd.run()
        if tmpfile:
            os.remove(tmpfile)
        return result.runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _cmdline(self, runtime):
        d = dict(
            in_file=self.inputs.in_file,
            out_file=self.inputs.out_file,
            img_type=self.inputs.img_type,
        )
        if len(self.inputs.indices) == 0:
            tmpfile = False
            script = Template(
                """
                library(neurobase)
                library(WhiteStripe)
                in_file = readnii('$in_file')
                ind = whitestripe(in_file, "$img_type")$$whitestripe.ind
                norm = whitestripe_norm(in_file, ind)
                out_file = '$out_file'
                writenii(norm, out_file)
                """
            ).substitute(d)
        else:
            # d['indices'] = ",".join(map(str, self.inputs.indices))
            tmpfile = tempfile.mkstemp()[1]
            self._write_indices(tmpfile, self.inputs.indices)
            d["indices"] = tmpfile
            script = Template(
                """
                library(neurobase)
                library(WhiteStripe)
                in_file = readnii('$in_file')
                # ind = c($indices)
                ind = as.vector(read.table("$indices")[[1]], mode='numeric')
                norm = whitestripe_norm(in_file, ind)
                out_file = '$out_file'
                writenii(norm, out_file)
                """
            ).substitute(d)

        return tmpfile, script

    def gen_indices(self):
        path = tempfile.mkstemp()[1]
        d = dict(
            in_file=self.inputs.in_file, out_file=path, img_type=self.inputs.img_type
        )
        script = Template(
            """
            library(neurobase)
            library(WhiteStripe)
            in_file = readnii('$in_file')
            t1_ind = whitestripe(in_file, "$img_type")$$whitestripe.ind
            write.table(t1_ind, file = "$out_file", row.names = F, col.names = F)
            """
        ).substitute(d)
        RCommand(script=script, rfile=False).run()
        ret = self._read_indices(path)
        os.remove(path)
        return ret

    def _read_indices(self, fn):
        with open(fn) as f:
            # read lines as ints
            return list(map(int, f))

    def _write_indices(self, fn, indices):
        with open(fn, "w") as f:
            for idx in indices:
                f.write("{}\n".format(idx))


if __name__ == "__main__":
    w = WhiteStripe()
    w.inputs.img_type = "T1"
    w.inputs.in_file = "T1W.nii.gz"
    # w.inputs.indices = [1,2,3]
    w.inputs.indices = w.gen_indices()
    w.inputs.out_file = "T1W_ws.nii.gz"
    w.run()
