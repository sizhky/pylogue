.PHONY: clean clean-build clean-pyc clean-test coverage dist docs help install lint lint/flake8 test

.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint/flake8: ## check style with flake8
	flake8 pylogue tests


lint: lint/flake8 ## check style

test: ## run tests quickly with the default Python
	pytest tests

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source pylogue -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

publish: clean ## build and publish package to PyPI (using sizhky account)
	python -m build
	python -m twine upload --repository sizhky dist/*

publish-divami: clean ## build and publish package to PyPI (using divami account)
	python -m build
	python -m twine upload --repository divami dist/*

publish-test: clean ## build and publish package to TestPyPI
	python -m build
	python -m twine upload --repository testpypi dist/*

install: clean ## install the package to the active Python's site-packages
	python setup.py install

docs:
	mkdocs build

serve-docs: docs ## serve the documentation with mkdocs
	uv run mkdocs serve

e:
	nbdev_export

setup:
	git init
	git add .
	git commit -m "Initial commit"
	uv sync