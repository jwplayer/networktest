test:
	python setup.py test

lint:
	python setup.py test --addopts '--flake8 nettest tests'
