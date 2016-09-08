# Makefile for building distributions of nipype.
# Files are then pushed to sourceforge using rsync with a command like this:
# rsync -e ssh nipype-0.1-py2.5.egg cburns,nipy@frs.sourceforge.net:/home/frs/project/n/ni/nipy/nipype/nipype-0.1/

PYTHON ?= python
NOSETESTS ?= nosetests

.PHONY: zipdoc sdist egg upload_to_pypi trailing-spaces clean-pyc clean-so clean-build clean-ctags clean in inplace test-code test-doc test-coverage test html specs check-before-commit check

zipdoc: html
	zip documentation.zip doc/_build/html

sdist: zipdoc
	@echo "Building source distribution..."
	python setup.py sdist
	@echo "Done building source distribution."
	# XXX copy documentation.zip to dist directory.

egg: zipdoc
	@echo "Building egg..."
	python setup.py bdist_egg
	@echo "Done building egg."

upload_to_pypi: zipdoc
	@echo "Uploading to PyPi..."
	python setup.py sdist --formats=zip,gztar upload

trailing-spaces:
	find . -name "*[.py|.rst]" -type f | xargs perl -pi -e 's/[ \t]*$$//'
	@echo "Reverting test_docparse"
	git checkout nipype/utils/tests/test_docparse.py

clean-pyc:
	find . -name "*.pyc" | xargs rm -f

clean-so:
	find . -name "*.so" | xargs rm -f
	find . -name "*.pyd" | xargs rm -f

clean-build:
	rm -rf build

clean-ctags:
	rm -f tags

clean-doc:
	rm -rf doc/_build

clean-tests:
	rm -f .coverage

clean: clean-build clean-pyc clean-so clean-ctags clean-doc clean-tests

in: inplace # just a shortcut
inplace:
	$(PYTHON) setup.py build_ext -i

test-code: in
	$(NOSETESTS) -s nipype --with-doctest --with-doctest-ignore-unicode

test-doc:
	$(NOSETESTS) -s --with-doctest --with-doctest-ignore-unicode --doctest-tests --doctest-extension=rst \
	--doctest-fixtures=_fixture doc/

test-coverage: clean-tests in
	$(NOSETESTS) -s --with-doctest --with-doctest-ignore-unicode --with-coverage --cover-package=nipype \
	--config=.coveragerc

test: clean test-code

html:
	@echo "building docs"
	make -C doc clean htmlonly

specs:
	@echo "Checking specs and autogenerating spec tests"
	python tools/checkspecs.py

check: check-before-commit # just a shortcut
check-before-commit: specs trailing-spaces html test
	@echo "removed spaces"
	@echo "built docs"
	@echo "ran test"
	@echo "generated spec tests"
