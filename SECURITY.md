# Security Practices

## Credentials & Secrets
- Use SSO or role-based auth; **no static keys** committed.
- Do not print credentials or tokens. Logs redact PII/secrets.
- Use `.secrets.baseline` with detect-secrets. Never commit real secrets.

## Least Privilege
- IAM role for Cognito identities restricts DynamoDB access by `dynamodb:LeadingKeys` == caller `sub`.
- Example minimal IAM for running local scripts is in `docs/policies/boto3-script-min-perms.json`.

## Transport & Encryption
- DynamoDB + Cognito use TLS by default. If you add S3/KMS, enable **SSE-KMS** and block public access.

## Dependency & Supply Chain
- Pin versions in `requirements*.txt`. Use `pre-commit` with **ruff/black/bandit/detect-secrets**.
- CI runs lint, format check, Bandit, and tests on PRs.

## Logging
- Structured logging; avoid sensitive fields. Prefer CloudWatch for infra logs.

## Runtime Hardening
- For Lambdas, enable code signing (optional) and least-privilege execution roles.
- Consider VPC endpoints for private-service access where applicable.

## Teardown & Cost
- `cdk destroy` removes resources. Always verify no data is required before teardown.