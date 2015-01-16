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
* Use a descriptive prefix for your PR: ENH, FIX, TST, DOC, STY, REF (refactor), WIP (Work in progress)
* After submiting the PR, include an update to the CHANGES file: prefix: description (URL of pull request)
* `make specs`
* do: `make check-before-commit` before submitting the PR. This will require you to either install or be in developer mode with: `python setup.py install/develop`.

## Contributing issues

When opening a new Issue, please take the following steps:

1. Search GitHub and/or [Neurostars](neurostars.org) for your issue to avoid duplicate reports.
   Keyword searches for your error messages are most helpful.
2. If possible, try updating to master and reproducing your issue,
   because we may have already fixed it.
3. OS and version
4. Nipype version
5. Output of: `import nipype; nipype.get_info()`
6. Versions of underlying tools (e.g., ANTS, FSL, SPM, etc.,.)
7. Any script, or output log, in a gist (gist.github.com)
8. When applicable, and where possible, pointers to relevant data files.
