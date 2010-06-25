=====================
Developing interfaces
=====================

The aim of this section is to describe how external programs and scripts can be
wrapped for use in Nipype either as interactive interfaces or within the
workflow/pipeline environment. Currently, there is support for command line
executables/scripts and matlab scripts. One can also create pure Python
interfaces. The key to defining interfaces is to provide a formal specification
of inputs and outputs and determining what outputs are generated given a set of
inputs.

Base and helper classes
=======================

* InterfaceBase
* CommandLine
* MatlabCommand
* FSLCommand
* FSCommand
* SPMCommand
* IOBase

Spec Base classes
=================

* TraitedSpec
* DynamicTraitedSpec
* CommandLineInputSpec

Three components of an interface
================================

* InputSpec
* OutputSpec
* Interface

