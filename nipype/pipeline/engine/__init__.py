#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Package contains modules for generating pipelines using interfaces

"""

__docformat__ = "restructuredtext"
from .workflows import Workflow
from .nodes import Node, MapNode, JoinNode
from .utils import generate_expanded_graph
