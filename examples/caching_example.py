"""
==============================
Caching without using Workflow
==============================

Using nipype in an imperative way: caching without workflow

Note that in the following example, we are calling command-lines with
disk I/O that persists across runs, but we never have to worry about the
file names or the directories.

The disk location of the persistence is encoded by hashes. To find out
where an operation has been persisted, simply look in it's output
variable::

    out.runtime.cwd
"""

from nipype.interfaces import fsl
fsl.FSLCommand.set_default_output_type('NIFTI')

from nipype.caching import Memory

import glob

# First retrieve the list of files that we want to work upon
in_files = glob.glob('data/*/f3.nii')

# Create a memory context
mem = Memory('.')

# Apply an arbitrary (and pointless, here) threshold to the files)
threshold = [mem.cache(fsl.Threshold)(in_file=f, thresh=i)
                        for i, f in enumerate(in_files)]

# Merge all these files along the time dimension
out_merge = mem.cache(fsl.Merge)(dimension="t",
                            in_files=[t.outputs.out_file for t in threshold],
                        )
# And finally compute the mean
out_mean = mem.cache(fsl.MeanImage)(in_file=out_merge.outputs.merged_file)

# To avoid having increasing disk size we can keep only what was touched
# in this run
#mem.clear_previous_runs()

# or what wasn't used since the start of 2011
#mem.clear_runs_since(year=2011)



