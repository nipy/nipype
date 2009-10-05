# Makefile for building distributions of nipype.

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

egg: zipdoc
	@echo "Building egg..."
	python setup.py bdist_egg
	@echo "Done building egg."