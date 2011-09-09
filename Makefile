# Makefile for building distributions of nipype.
# Files are then pushed to sourceforge using rsync with a command like this:
# rsync -e ssh nipype-0.1-py2.5.egg cburns,nipy@frs.sourceforge.net:/home/frs/project/n/ni/nipy/nipype/nipype-0.1/

PYTHON ?= python
NOSETESTS ?= nosetests

zipdoc:
	@echo "Clean documentation directory."
	python setup.py clean
	@echo "Build documentation.zip..."
	python setup.py build_sphinx
	@echo "Clean documentation directory."
	python setup.py clean

sdist: zipdoc
	@echo "Building source distribution..."
	python setup.py sdist
	@echo "Done building source distribution."
	# XXX copy documentation.zip to dist directory.
	# XXX Somewhere the doc/_build directory is removed and causes
	# this script to fail.

egg: zipdoc
	@echo "Building egg..."
	python setup.py bdist_egg
	@echo "Done building egg."

upload_to_pypi: zipdoc
	@echo "Uploading to PyPi..."
	python setup.py sdist --formats=zip,gztar upload

trailing-spaces:
	find . -name "*.py" | xargs perl -pi -e 's/[ \t]*$$//'

clean-pyc:
	find . -name "*.pyc" | xargs rm -f

clean-so:
	find . -name "*.so" | xargs rm -f
	find . -name "*.pyd" | xargs rm -f

clean-build:
	rm -rf build

clean-ctags:
	rm -f tags

clean: clean-build clean-pyc clean-so clean-ctags

in: inplace # just a shortcut
inplace:
	$(PYTHON) setup.py build_ext -i

test-code: in
	$(NOSETESTS) -s nipype --with-doctest
	stty sane

test-doc:
	$(NOSETESTS) -s --with-doctest --doctest-tests --doctest-extension=rst \
	--doctest-fixtures=_fixture doc/
	stty sane

test-coverage:
	$(NOSETESTS) -s --with-doctest --with-coverage --cover-html --cover-html-dir=coverage \
	--cover-package=nipype nipype
	stty sane

test: test-code

