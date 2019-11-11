test:
	python setup.py test --addopts '--cov=networktest --cov-fail-under=70'

lint:
	python setup.py test --addopts '--flake8 networktest tests'

coverage:
	python setup.py test --addopts '--cov=networktest --cov-report=html'
	open htmlcov/index.html
