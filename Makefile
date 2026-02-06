.PHONY: help clean clean-build clean-pyc clean-test lock sync tree lint format typecheck test coverage bump-patch bump-minor bump-major build publish publish-divami publish-test docs serve-docs

.DEFAULT_GOAL := help

UV ?= uv

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z0-9_./-]+):.*?## (.*)$$', line)
	if match:
		target, help_text = match.groups()
		print(f"{target:20s} {help_text}")
endef
export PRINT_HELP_PYSCRIPT

help: ## show this help message
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove build, cache, and test artifacts

clean-build: ## remove build artifacts
	rm -rf build/ dist/ .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -rf {} +

clean-pyc: ## remove Python bytecode artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

clean-test: ## remove test and coverage artifacts
	rm -rf .tox/ htmlcov/ .pytest_cache/
	rm -f .coverage

lock: ## update uv.lock from pyproject.toml
	$(UV) lock

sync: ## sync local environment with lockfile and all extras
	$(UV) sync --all-extras

tree: ## show dependency tree
	$(UV) tree

lint: ## run linter
	$(UV) run ruff check .

format: ## format code
	$(UV) run ruff format .

typecheck: ## run mypy type checks
	$(UV) run mypy .

test: ## run test suite
	$(UV) run pytest tests

coverage: ## run tests with coverage report
	$(UV) run coverage run --source src/pylogue -m pytest tests
	$(UV) run coverage report -m

build: clean-build ## build source and wheel distributions
	rm -rf dist/ build/ *.egg-info
	python -m build
	ls -l dist

publish: build ## upload to PyPI (repository: sizhky)
	python -m twine upload --repository sizhky dist/*

publish-divami: build ## upload to PyPI (repository: divami)
	python -m twine upload --repository divami dist/*

publish-test: build ## upload to TestPyPI
	python -m twine upload --repository testpypi dist/*

bump-patch: ## bump Python package version (patch)
	$(UV) version --bump patch

bump-minor: ## bump Python package version (minor)
	$(UV) version --bump minor

bump-major: ## bump Python package version (major)
	$(UV) version --bump major

docs: ## build documentation
	$(UV) run mkdocs build

serve-docs: ## serve documentation locally
	$(UV) run mkdocs serve
