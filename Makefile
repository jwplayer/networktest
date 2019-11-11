test:
	python setup.py test --addopts '--cov=nettest --cov-fail-under=70'

lint:
	python setup.py test --addopts '--flake8 nettest tests'

coverage:
	python setup.py test --addopts '--cov=nettest --cov-report=html'
	open htmlcov/index.html
