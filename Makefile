SHELL := /bin/bash

.PHONY: venv synth diff deploy destroy ddb-demo simulate fmt lint security

venv:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt -r requirements-dev.txt

synth:
	. .venv/bin/activate && cdk synth

diff:
	. .venv/bin/activate && cdk diff

deploy:
	. .venv/bin/activate && cdk deploy

destroy:
	. .venv/bin/activate && cdk destroy

ddb-demo:
	. .venv/bin/activate && python scripts/boto3/ddb_user_demo.py

simulate:
	. .venv/bin/activate && python scripts/boto3/policy_simulate.py

fmt:
	. .venv/bin/activate && black src scripts

lint:
	. .venv/bin/activate && ruff check src scripts

security:
	. .venv/bin/activate && bandit -c pyproject.toml -r src scripts
	. .venv/bin/activate && detect-secrets scan --baseline .secrets.baseline
