**Are you new to open source and GitHub?** If so reading the "[How to submit a contribution](https://opensource.guide/how-to-contribute/#how-to-submit-a-contribution)" guide will provide a great introduction to contributing to Nipype and other Open Source projects. All the Nipype specific contributing instructions listed below will make much more sense after reading this guide.

## Contributing pull-requests (PRs)

* All work is submitted via Pull Requests.
* Pull Requests can be submitted as soon as there is code worth discussing.
  Pull Requests track the branch, so you can continue to work after the PR is submitted.
  Review and discussion can begin well before the work is complete,
  and the more discussion the better.
  The worst case is that the PR is closed.
* Pull Requests should generally be made against master
* Pull Requests should be tested, if feasible:
    - bugfixes should include regression tests
    - new behavior should at least get minimal exercise
* Use a descriptive prefix for your PR: ENH (enhancement), FIX, TST, DOC, STY, REF (refactor), WIP (Work in progress)
* The person who accepts/merges your PR will include an update to the CHANGES file: prefix: description (URL of pull request)
* Run `make check-before-commit` before submitting the PR.
  This will require you to either install or be in developer mode with: `python setup.py install/develop`.
* In general, do not catch exceptions without good reason. 
  * catching non-fatal exceptions. 
    Log the exception as a warning.
  * adding more information about what may have caused the error.
    Raise a new exception using ``raise_from(NewException("message"), oldException)`` from ``future``.
    Do not log this, as it creates redundant/confusing logs.
* **If you are new to the project don't forget to add your name and affiliation to the `.zenodo.json` file.**

## Contributing issues

When opening a new Issue, please take the following steps:

1. Search GitHub and/or [Neurostars](http://neurostars.org) for your issue to avoid duplicate reports.
   Keyword searches for your error messages are most helpful.
2. If possible, try updating to master and reproducing your issue,
   because we may have already fixed it.
3. OS and version
4. Nipype version
5. Output of: `import nipype; nipype.get_info()`
6. Versions of underlying tools (e.g., ANTS, FSL, SPM, etc.,.)
7. Any script, or output log, in a gist (gist.github.com)
8. When applicable, and where possible, pointers to relevant data files.
