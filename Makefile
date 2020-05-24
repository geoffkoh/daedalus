all: lint test

lint:
	pylint -v src

typcheck:
	mypy src

test:
	PYTHONPATH=src \
	pytest -sv tests
	