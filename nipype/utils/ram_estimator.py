import nibabel as nib
import math
from ..interfaces.base import isdefined
import os


class RamEstimator:
    """
    Base class for Nipype RAM estimators.

    A RamEstimator provides a lightweight, user-defined mechanism to
    estimate the peak RAM usage (in GB) of a Nipype node *before execution*,
    based on the node inputs.

    The estimator aggregates RAM contributions from selected input traits
    using user-defined multipliers and returns:

    - an estimated RAM value (mem_gb)
    - a human-readable debug string describing the estimate

    The estimator is intended to be attached to a Node or MapNode via the
    ``node.ram_estimator`` attribute and is evaluated automatically when
    executing workflows with the ``MultiProcPlugin``.

    Notes
    -----
    * The estimator is only used when running a workflow with
      ``MultiProcPlugin`` (or subclasses thereof).
    * For ``MapNode`` instances, the estimator is inherited by all subnodes
      and evaluated on a *single representative iteration*.
      The resulting ``mem_gb`` is interpreted as the per-task memory
      requirement (i.e., the worst-case memory for one mapped job).
    * The debug string produced by the estimator is stored in the node
      runtime report (``_report/report.rst``) under the ``runtime`` section.

    Examples
    --------
    Define a tool-specific RAM estimator and attach it to a node::

        class FlirtRamEstimator(RamEstimator):
            def __init__(self):
                super().__init__(
                    input_multipliers={
                        'in_file': 32,
                        'reference': 4,
                    },
                    overhead_gb=0.3,
                    min_gb=0.5,
                    max_gb=4.0
                )

        from nipype.interfaces.fsl import FLIRT
        from nipype.pipeline.engine import Node

        flirt = Node(
            FLIRT(dof=6),
            name="flirt"
        )

        flirt.ram_estimator = FlirtRamEstimator()
    """

    def __init__(
        self,
        input_multipliers=None,
        overhead_gb=0.3,
        min_gb=0.5,
        max_gb=8.0
    ):
        """
        Parameters
        ----------
        input_multipliers : dict, optional
            Mapping ``input_name -> multiplier``.

            The interpretation of the multiplier depends on the input type:

            * File-like image inputs:
              ``multiplier`` scales with the total number of spatial voxels.
              The contribution is computed as::

                  contribution_gb = voxels * multiplier / 1024**3

            * Numeric inputs (int, float, or lists thereof):
              ``multiplier`` scales linearly with the numeric value(s).

            The choice of multipliers is tool-specific and left to the user.

        overhead_gb : float, optional
            Fixed RAM overhead (in GB) added to the estimate to account for
            control structures, buffers, and library overhead.

        min_gb : float, optional
            Minimum allowed RAM estimate (GB).

        max_gb : float, optional
            Maximum allowed RAM estimate (GB).
        """

        self.input_multipliers = input_multipliers or {}
        self.overhead_gb = overhead_gb
        self.min_gb = min_gb
        self.max_gb = max_gb

    @staticmethod
    def voxels(path):
        """Return number of spatial voxels (ignores time dimension)."""
        img = nib.load(path)
        shape = img.header.get_data_shape()
        return math.prod(shape[:3])

    @staticmethod
    def clamp(value, min_val=None, max_val=None):
        """Clamp a value between min_val and max_val."""
        if min_val is not None:
            value = max(min_val, value)
        if max_val is not None:
            value = min(max_val, value)
        return value

    def __call__(self, inputs):
        """
        Estimate RAM usage based on Nipype input traits.

        - File-like image inputs contribute via voxel count
        - Numeric inputs contribute via their numeric value
        - Lists are supported for both files and numbers

        Returns
        -------
        mem_gb : float
            Estimated RAM in GB
        estimator_string : str
            Debug string for node report
        """
        total_gb = 0.0
        debug_lines = []

        traits = inputs.traits()

        for attr, multiplier in self.input_multipliers.items():
            if attr not in traits:
                debug_lines.append(f"{attr}: trait not found")
                continue

            val = getattr(inputs, attr, None)

            if not isdefined(val) or val is None:
                debug_lines.append(f"{attr}: undefined")
                continue

            # --------------------------------------------------
            # FILE-LIKE VALUES (string or list/tuple of strings)
            # --------------------------------------------------
            paths = None

            if isinstance(val, str):
                paths = [val]

            elif isinstance(val, (list, tuple)) and any(isinstance(v, str) for v in val):
                paths = [v for v in val if isinstance(v, str)]

            if paths is not None:
                vox_total = 0
                valid_files = 0

                for p in paths:
                    if not isinstance(p, str) or not os.path.exists(p):
                        continue
                    try:
                        vox_total += self.voxels(p)
                        valid_files += 1
                    except Exception:
                        # exists but not a readable image (e.g. txt)
                        continue

                if valid_files > 0:
                    contribution = vox_total * multiplier / (1024 ** 3)
                    total_gb += contribution

                    debug_lines.append(
                        f"{attr}: voxels={vox_total}, multiplier={multiplier}, "
                        f"contribution={contribution:.3f} GB"
                    )
                else:
                    debug_lines.append(f"{attr}: no readable image files")

                continue

            # --------------------------------------------------
            # NUMERIC VALUES (scalar or list/tuple of numbers)
            # --------------------------------------------------
            values = None

            if isinstance(val, (int, float)):
                values = [val]

            elif isinstance(val, (list, tuple)) and all(isinstance(v, (int, float)) for v in val):
                values = val

            if values is not None:
                contribution = sum(float(v) for v in values) * multiplier
                total_gb += contribution

                debug_lines.append(
                    f"{attr}: values={values}, multiplier={multiplier}, "
                    f"contribution={contribution:.3f} GB"
                )
                continue

            # --------------------------------------------------
            # UNSUPPORTED TYPE
            # --------------------------------------------------
            debug_lines.append(
                f"{attr}: unsupported value type ({type(val).__name__})"
            )

        # ------------------------------------------------------
        # OVERHEAD + CLAMP
        # ------------------------------------------------------
        mem_gb = total_gb + self.overhead_gb
        debug_lines.append(
            f"Overhead={self.overhead_gb} GB, total estimated RAM={mem_gb:.3f} GB"
        )

        mem_gb = self.clamp(mem_gb, self.min_gb, self.max_gb)
        debug_lines.append(f"Clamp={mem_gb:.3f} GB")

        estimator_string = " | ".join(debug_lines)
        return float(mem_gb), estimator_string