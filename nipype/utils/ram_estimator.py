import nibabel as nib
import math
from dataclasses import dataclass, field
from ..interfaces.base import isdefined
import os


@dataclass
class RamPlan:
    """
    Outcome of a bidirectional RAM negotiation for a single node.

    Instances are returned by :meth:`RamEstimator.negotiate`, and applied to
    the node by the ``MultiProc`` plugin before the node is scheduled.

    Attributes
    ----------
    mem_gb : float
        RAM reservation (GB) to set on the node, after tuning.
    tuned_params : dict
        Node input values to apply so that the estimated peak fits the RAM
        budget (e.g. thread count, chunk size). Empty if nothing is tuned.
        The special key ``environ`` is merged into ``inputs.environ``.
    n_procs : int or None
        CPU reservation consistent with the tuned parameters. ``None`` keeps
        the node's declared value.
    debug_str : str
        Human-readable trace of the negotiation, stored in the node report.

    Examples
    --------
    A plan that reserves 2 GB and runs the node with 4 threads::

        RamPlan(
            mem_gb=2.0,
            tuned_params={'num_threads': 4},
            n_procs=4,
            debug_str="num_threads=4",
        )
    """

    mem_gb: float
    tuned_params: dict = field(default_factory=dict)
    n_procs: int = None
    debug_str: str = ""


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
    * Estimators can also take part in a *bidirectional* negotiation by
      overriding :meth:`RamEstimator.negotiate`: besides reserving RAM, they
      can tune node parameters so that the estimated peak fits the RAM budget
      of the plugin (see :class:`RamPlan`).

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

    Override :meth:`negotiate` to tune a node to the RAM budget of the
    plugin (``memory_gb``). The following estimator lowers the number of
    threads of a (hypothetical) tool until its estimated peak fits::

        class ThreadedToolRamEstimator(RamEstimator):
            def __init__(self):
                super().__init__(input_multipliers={'in_file': 16})

            def negotiate(self, inputs, ram_budget_gb):
                base_gb, debug_str = self(inputs)
                for num_threads in (8, 4, 2, 1):
                    # each thread needs a private copy of the working buffers
                    mem_gb = base_gb * (1 + 0.5 * num_threads)
                    if mem_gb <= ram_budget_gb:
                        break
                return RamPlan(
                    mem_gb=mem_gb,
                    tuned_params={'num_threads': num_threads},
                    n_procs=num_threads,
                    debug_str=f"{debug_str} | num_threads={num_threads}",
                )

    The plan is applied by the ``MultiProc`` plugin right before the node is
    scheduled: ``tuned_params`` are set on the node inputs, ``mem_gb`` and
    ``n_procs`` become the resources reserved for the node, and
    ``debug_str`` is stored in the node report.
    """

    def __init__(self, input_multipliers=None, overhead_gb=0.3, min_gb=0.5, max_gb=8.0):
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

            elif isinstance(val, (list, tuple)) and any(
                isinstance(v, str) for v in val
            ):
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
                    contribution = vox_total * multiplier / (1024**3)
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

            elif isinstance(val, (list, tuple)) and all(
                isinstance(v, (int, float)) for v in val
            ):
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
            debug_lines.append(f"{attr}: unsupported value type ({type(val).__name__})")

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

    def negotiate(self, inputs, ram_budget_gb):
        """
        Negotiate RAM reservation and node tuning against a RAM budget.

        Besides reserving RAM, an estimator may tune quality-neutral node
        parameters so that the estimated peak fits ``ram_budget_gb`` (the
        memory the executing plugin is allowed to use). The default
        implementation does not tune anything: it wraps ``__call__``.
        Subclasses can override it, e.g. to walk an ordered ladder of
        configurations and return the first one that fits the budget; if no
        configuration fits, the most frugal one should be returned.

        The method is called by the ``MultiProc`` plugin when the node is
        about to be scheduled, so that the inputs of the node are available.
        It is not called for ``MapNode`` instances submitted whole, whose
        iterfield inputs are lists; their subnodes inherit the estimator
        and are negotiated one by one.

        Parameters
        ----------
        inputs : BaseTraitedSpec
            Node inputs, as passed to ``__call__``.
        ram_budget_gb : float
            RAM budget (GB) available to the plugin.

        Returns
        -------
        plan : RamPlan
        """
        mem_gb, debug_str = self(inputs)
        return RamPlan(mem_gb=mem_gb, debug_str=debug_str)
