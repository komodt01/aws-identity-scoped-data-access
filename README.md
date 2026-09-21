# AWS Identity-Scoped Data Access

## Overview

This project demonstrates an AWS security architecture for restricting application data access according to an authenticated identity.

The central security question is:

> How can an authenticated user be allowed to access only the data associated with that identity without relying solely on application authorization logic?

The architecture combines Amazon Cognito, Cognito Identity Pools, AWS STS, IAM, and DynamoDB to establish an identity-aware authorization path.

The core principle is:

> Authentication establishes identity. Authorization determines what that identity can access.

---

## Security Objective

The intended security boundary is:

```text
Identity A -> Identity A data -> ALLOW
Identity A -> Identity B data -> DENY
```

Rather than allowing the application alone to determine data ownership, the design introduces an additional authorization control through IAM and the DynamoDB partition-key model.

This creates defense in depth between authentication and access to application data.

---

## Architecture

The implemented architecture is:

```text
Application User
       |
       v
Cognito User Pool
       |
       v
User Pool Client
       |
       v
Cognito Identity Pool
       |
       v
AWS STS
Temporary Credentials
       |
       v
Authenticated IAM Role
       |
       v
IAM Authorization
dynamodb:LeadingKeys
       |
       v
DynamoDB
Identity-Scoped Partition
```

Each component performs a separate security function.

### Cognito User Pool

Provides application-user authentication.

### User Pool Client

Represents the application interaction with the User Pool.

### Cognito Identity Pool

Connects the authenticated application identity to AWS authorization.

Unauthenticated identities are disabled.

### AWS STS

Provides temporary AWS credentials associated with the authenticated role rather than requiring long-lived AWS credentials in application code.

### IAM

Defines the actions the temporary credentials are authorized to perform and applies an identity-based condition to DynamoDB access.

### DynamoDB

Stores application data using `userId` as the partition key.

The IAM authorization policy uses `dynamodb:LeadingKeys` to constrain access according to the Cognito identity associated with the temporary credentials.

---

## What Is Implemented

The AWS CDK stack provisions:

- Amazon Cognito User Pool
- Cognito User Pool Client
- Cognito Identity Pool
- IAM role for authenticated identities
- IAM trust relationship scoped to the Identity Pool and authenticated context
- DynamoDB table using `userId` as the partition key
- IAM policy permitting required DynamoDB operations
- `dynamodb:LeadingKeys` authorization condition
- Identity Pool role attachment
- CloudFormation outputs for deployed resource identifiers

The repository also contains supporting Python scripts for:

- Basic DynamoDB interaction
- IAM policy simulation

Infrastructure is defined in Python using AWS CDK and synthesized into AWS CloudFormation.

---

## Authorization Model

Authentication and authorization are deliberately separated.

Successful authentication does not automatically grant unrestricted data access.

The authenticated role permits only:

- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`

Those permissions are restricted to the DynamoDB table created by the stack.

An additional IAM condition uses:

```text
dynamodb:LeadingKeys
```

with the Cognito identity context.

The resulting authorization model is intended to constrain an authenticated identity to its corresponding data partition.

This provides an enforcement layer at the AWS authorization boundary rather than relying entirely on application code.

---

## IAM Trust Boundary

The authenticated IAM role is designed to be assumed only through the configured Cognito Identity Pool.

The trust relationship checks:

- The expected Cognito Identity Pool
- Authenticated identity context

Unauthenticated Identity Pool access is disabled.

Changes to this trust relationship are security-sensitive because broadening the role assumption path could weaken the authorization architecture even if the DynamoDB policy itself remains unchanged.

---

## Least Privilege

Least privilege is applied at several levels:

```text
AWS Service
    |
    v
Specific DynamoDB Table
    |
    v
Required Data Operations
    |
    v
Identity-Scoped Partition
```

The authenticated role does not receive broad DynamoDB administrative permissions.

Operations such as table creation, table deletion, and table scanning are not required by the demonstrated access pattern.

The design therefore constrains:

1. Which service can be accessed.
2. Which resource can be accessed.
3. Which actions can be performed.
4. Which data partition the identity should be able to access.

---

## Security Validation

The repository currently validates several parts of the architecture.

### CI Validation

GitHub Actions performs:

- Ruff linting
- Black formatting validation
- Bandit static security analysis
- Secret detection
- CDK synthesis

These checks currently pass for the repository.

Successful CDK synthesis verifies that the infrastructure definition can be converted into CloudFormation, but it does not prove runtime authorization behavior.

### IAM Policy Simulation

The policy simulation script supports examination of the IAM authorization model and the context used by the identity-scoped policy.

Policy simulation is useful architecture validation, but it is not equivalent to authenticating through Cognito and exercising the authorization boundary at runtime.

### DynamoDB Demonstration

The DynamoDB script performs basic data-plane interaction using the caller's existing AWS credentials.

It demonstrates DynamoDB interaction but does not independently prove Cognito-based identity isolation.

### Runtime Validation Still Required

A stronger end-to-end validation would authenticate separate Cognito identities, obtain temporary AWS credentials through the Identity Pool, and demonstrate:

```text
Identity A -> Identity A data -> ALLOW

Identity A -> Identity B data -> DENY
```

The denied request is especially important because an authorization control should be validated through negative testing as well as successful access.

This end-to-end Cognito runtime test is not currently implemented in the repository.

---

## Control Failure Scenarios

The intended security boundary depends on multiple controls operating together.

It could be weakened by:

- Broadening the IAM trust relationship
- Allowing unauthenticated Identity Pool access
- Removing the `dynamodb:LeadingKeys` condition
- Expanding DynamoDB permissions unnecessarily
- Incorrectly associating identities with data partitions
- Trusting application-supplied identity values instead of established identity context
- Misconfiguring Cognito federation
- Changing Identity Pool role mappings

These are security architecture changes rather than simply infrastructure changes.

A syntactically valid infrastructure deployment can still contain an incorrect authorization design.

---

## Secure Development Controls

The repository includes development controls supporting the infrastructure and Python code.

### GitHub Actions Security CI

The CI workflow performs:

```text
Ruff
  ↓
Black
  ↓
Bandit
  ↓
Secret Detection
  ↓
CDK Synthesis
```

Failures stop the workflow rather than being silently ignored.

### Pre-Commit Controls

The repository also includes pre-commit configuration for:

- Black
- Ruff
- Bandit
- detect-secrets

These controls reduce the likelihood of formatting problems, common Python security issues, and accidental secret exposure entering the repository.

They support the architecture but do not replace runtime security testing.

---

## Infrastructure Workflow

The normal CDK workflow is:

```bash
make synth
make diff
make deploy
```

or directly:

```bash
cdk synth
cdk diff
cdk deploy
```

`cdk synth` generates the CloudFormation representation of the architecture.

`cdk diff` should be reviewed before changes are deployed, particularly when changes affect:

- IAM permissions
- IAM trust relationships
- Cognito configuration
- Identity Pool role mappings
- DynamoDB authorization conditions

For the disposable demonstration environment:

```bash
cdk destroy
```

can be used to remove stack resources.

---

## Architecture Tradeoffs

### IAM Enforcement vs Application-Only Authorization

Adding IAM-based data authorization creates another enforcement layer but also increases architecture complexity.

The relationship among application identity, Cognito identity, IAM conditions, and the DynamoDB data model must remain consistent.

### Fine-Grained Access vs Operational Complexity

Identity-scoped authorization can reduce the blast radius of unauthorized access.

More granular authorization models, however, require careful policy management, identity mapping, testing, and monitoring.

### Temporary Credentials vs Identity Dependency

Temporary credentials reduce reliance on long-lived AWS credentials.

The architecture consequently depends on the availability and correct configuration of the identity and federation services.

Those dependencies would require operational and recovery planning in a production system.

---

## Production Considerations

This project demonstrates a focused identity and authorization pattern rather than a complete production identity platform.

A production implementation would require additional architecture decisions involving:

- MFA
- Account recovery
- Identity lifecycle management
- Session and token management
- Monitoring and alerting
- Audit logging and retention
- Data encryption requirements
- Backup and recovery
- Data retention
- Deletion protection
- Environment separation
- Privileged administration
- Incident response
- Availability and regional resilience

The stack also uses resource-removal behavior appropriate for disposable demonstration infrastructure.

Production data should use retention, backup, recovery, and deletion controls based on explicit business and security requirements.

---

## Residual Risk

Identity-scoped authorization reduces the risk of one authenticated identity accessing another identity's data through the protected DynamoDB path.

It does not eliminate:

- Credential or session theft
- Compromise of a legitimate user
- Application vulnerabilities
- Identity-provider misconfiguration
- Administrative misuse
- Authorization-policy drift
- Incorrect identity-to-data mapping
- Security weaknesses elsewhere in the application architecture

Additional preventive, detective, and operational controls would be required for a production environment.

---

## Repository Structure

```text
.github/workflows/
    security-ci.yml

docs/policies/
    boto3-script-min-perms.json

scripts/aws/
    ddb_user_demo.py
    policy_simulate.py

src/
    app.py
    identity_scoped_data_access_stack.py

README.md
SECURITY.md
deployment-workflow.md
technical-case-study.md
Makefile
cdk.json
pyproject.toml
requirements.txt
requirements-dev.txt
```

---

## Supporting Documentation

### `technical-case-study.md`

Provides the deeper Security Architecture analysis, including trust boundaries, least privilege, failure scenarios, validation strategy, tradeoffs, residual risk, and production considerations.

### `SECURITY.md`

Documents the project's security assumptions, control dependencies, failure scenarios, and secure-development considerations.

### `deployment-workflow.md`

Describes the CDK deployment lifecycle, security-sensitive change review, validation expectations, and production differences.

---

## Technologies

- Amazon Cognito
- Cognito Identity Pools
- AWS STS
- AWS IAM
- Amazon DynamoDB
- AWS CDK
- AWS CloudFormation
- Python
- boto3
- GitHub Actions
- Ruff
- Black
- Bandit
- detect-secrets

---

## Key Takeaway

Identity security does not end when a user successfully authenticates.

The more important architecture question is:

> What is that authenticated identity allowed to do next?

This project demonstrates an AWS architecture in which authentication establishes identity, temporary credentials carry that identity into AWS authorization, and IAM conditions constrain access at the data layer.

The remaining end-to-end validation step is to prove the intended boundary with separate authenticated Cognito identities and both permitted and denied runtime requests.
