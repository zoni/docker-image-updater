.PHONY: help test testlocal

ifneq ($(strip $(TOX_RECREATE)),)
TOX = tox --recreate
else
TOX = tox
endif

help:
	@echo "help:       Print this help message"
	@echo "test:       Run tests"
	@echo "testlocal:  Run tests locally without using tox"

test:
	@$(TOX)

testlocal:
	@py.test --cov diu --cov-report term --cov-report html --cov-report xml -v
	@flake8 --show-source --statistics
