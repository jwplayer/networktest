.PHONY: test lint coverage clean release

help:
	@echo "clean - remove build artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "release - package and upload a release"

test:
	python setup.py test --addopts '--cov=networktest --cov-fail-under=70'

lint:
	python setup.py test --addopts '--flake8 networktest tests'

coverage:
	python setup.py test --addopts '--cov=networktest --cov-report=html'
	open htmlcov/index.html

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

release: clean
	python setup.py sdist bdist_wheel
	twine upload dist/*
