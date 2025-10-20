# SEC-01 — IAM Zero-Trust Starter (CDK Python, no Terraform)

A Python-first implementation of per-user, least-privilege data access:
**Cognito (auth) → Identity Pool → STS AssumeRole → DynamoDB (user-only item)**.

- **Infra as Code:** AWS **CDK in Python** (no Terraform).
- **App/Validation:** Python (`boto3`) demo scripts.
- **Teardown:** `cdk destroy`.

## Why this matters
Identity-scoped access enforces **least-privilege**, reduces blast radius, and aligns to **NIST 800-53 AC-3/AC-6** and **ISO 27001 A.5.15**.

## What gets deployed
- Cognito **User Pool**
- Cognito **Identity Pool** (authenticated identities only)
- DynamoDB table `userId` (PK)
- IAM role for authenticated identities with policy:
  - Allow `PutItem`, `GetItem`, `UpdateItem` **only** when `dynamodb:LeadingKeys == ${cognito-identity.amazonaws.com:sub}`

## Layout
```
sec-01-iam-zero-trust-starter-cdk-python/
├─ README.md
├─ docs/
├─ src/
│  ├─ app.py                 # CDK entrypoint
│  └─ zero_trust_stack.py    # CDK stack (Cognito + DDB + IAM)
├─ scripts/
│  └─ boto3/
│     ├─ ddb_user_demo.py    # Put/Get for current userId
│     └─ policy_simulate.py  # IAM policy simulation
├─ requirements.txt
├─ requirements-dev.txt
├─ cdk.json
├─ Makefile
└─ tests/
```

## Prereqs
- Python 3.10+
- AWS credentials (profile or SSO)
- CDK CLI: `npm i -g aws-cdk` (one-time)
- Bootstrap once per account/region: `cdk bootstrap aws://<account>/<region>`

## Quickstart
```bash
make venv          # create .venv and install deps
make synth         # cdk synth (preview CFN)
make deploy        # cdk deploy (creates Cognito/DDB/IAM)
make ddb-demo      # write/read a per-user item via boto3
make simulate      # IAM policy simulation
make destroy       # cdk destroy
```

## Notes
- Replace `<ACCOUNT_ID>` and `<REGION>` in environment/export commands as needed.
- Evidence to capture: denied cross-user attempt, CloudTrail AssumeRole entries.

---

## Secure Python defaults
- **No hardcoded secrets**; authenticate via SSO or roles.
- **Retries & timeouts** configured in boto3 (`botocore.config.Config`) to avoid hanging calls.
- **Least-privilege** IAM examples in `docs/policies/boto3-script-min-perms.json`.
- **Pre-commit** hooks: ruff/black/bandit/detect-secrets (`pre-commit install`).
- **CI** runs lint, format checks, Bandit, detect-secrets, tests, and `cdk synth`.

```bash
pip install pre-commit && pre-commit install
# Scan for secrets locally
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline
```
