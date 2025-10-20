SHELL := /bin/bash

.PHONY: venv synth deploy destroy ddb-demo simulate fmt lint test

venv:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt -r requirements-dev.txt

synth:
	. .venv/bin/activate && cdk synth

deploy:
	. .venv/bin/activate && cdk deploy --require-approval never

destroy:
	. .venv/bin/activate && cdk destroy --force

ddb-demo:
	. .venv/bin/activate && python scripts/boto3/ddb_user_demo.py

simulate:
	. .venv/bin/activate && python scripts/boto3/policy_simulate.py

fmt:
	. .venv/bin/activate && black src scripts

lint:
	. .venv/bin/activate && ruff check src scripts

test:
	. .venv/bin/activate && pytest -q