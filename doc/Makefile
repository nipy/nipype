# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d _build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help clean html htmlonly latex changes linkcheck doctest

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html      make the HTML documentation"
	@echo "  latex     make the LaTeX, you can set PAPER=a4 or PAPER=letter"
	@echo "  pdf		make <latex> and run the PDF generation"
	@echo "  changes   make an overview of all changed/added/deprecated" \
	      		"items (ChangeLog)"
	@echo "  linkcheck check all external links for integrity"
	@echo "  doctest   run all doctests embedded in the documentation"
	@echo "  sf_satra copy html files to sourceforge (satra only)"

clean:
	-rm -rf _build/* *~ api/generated interfaces/generated users/examples documentation.zip

htmlonly:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) _build/html
	@echo
	@echo "Build finished. The HTML pages are in _build/html."

html: clean examples2rst htmlonly
	@echo "Build HTML and API finished."

examples2rst: clean
	mkdir -p users/examples
	../tools/make_examples.py -x ../../../examples/test_spm.py --no-exec
	@echo "examples2rst finished."

latex: clean examples2rst
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) _build/latex
	@echo
	@echo "Build finished; the LaTeX files are in _build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."
pdf: latex
	cd _build/latex && make all-pdf

all: html pdf

changes:
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) _build/changes
	@echo
	@echo "The overview file is in _build/changes."

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) _build/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in _build/linkcheck/output.txt."

doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) _build/doctest
	@echo "Testing of doctests in the sources finished, look at the " \
	      "results in _build/doctest/output.txt."

gitwash-update:
	python -u ../tools/gitwash_dumper.py devel nipype \
            --repo-name=nipype \
            --github-user=nipy \
            --project-url=http://nipy.org/nipype \
            --project-ml-url=http://mail.scipy.org/mailman/listinfo/nipy-devel
	@echo "gitwash updated"
