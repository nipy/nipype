

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
	@echo "Not implemented yet!"
	#@echo "Building egg..."
	#python setup_egg.py
	#@echo "Done building egg."