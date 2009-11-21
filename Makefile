# Makefile for building distributions of nipype.
# Files are then pushed to sourceforge using rsync with a command like this:
# rsync -e ssh nipype-0.1-py2.5.egg cburns,nipy@frs.sourceforge.net:/home/frs/project/n/ni/nipy/nipype/nipype-0.1/

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

