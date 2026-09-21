# AWS Identity-Scoped Data Access

## Overview

This project demonstrates how AWS identity and authorization controls can be combined to enforce per-user access to application data.

The implementation uses Amazon Cognito, Cognito Identity Pools, AWS STS, IAM, and DynamoDB to create an identity-scoped authorization path.

The central security objective is:

> An authenticated user should be able to access only the data associated with that user's identity.

## Architecture

The authorization flow is:

```text
User
  |
  v
Amazon Cognito User Pool
  |
  v
Cognito Identity Pool
  |
  v
AWS STS temporary credentials
  |
  v
IAM authenticated-user role
  |
  v
DynamoDB
  |
  v
Identity-scoped partition
```

Cognito establishes the user's identity.

The Cognito Identity Pool provides authenticated identities with a path to temporary AWS credentials.

AWS STS issues temporary credentials for the authenticated identity.

IAM defines what those credentials are authorized to do.

DynamoDB provides the data store, with an IAM condition restricting access based on the caller's Cognito identity.

## Security Objective

The project demonstrates a data-access boundary enforced through identity rather than application logic alone.

The IAM policy uses the DynamoDB `LeadingKeys` condition to restrict access to items whose partition key corresponds to the caller's Cognito identity.

This creates a security relationship between:

- The authenticated identity
- The temporary AWS credentials
- The IAM authorization policy
- The DynamoDB partition key

## What Is Implemented

The AWS CDK stack provisions:

- Amazon Cognito User Pool
- Amazon Cognito Identity Pool
- IAM role for authenticated identities
- IAM trust policy for Cognito identities
- DynamoDB table using `userId` as the partition key
- IAM policy restricting DynamoDB access with `dynamodb:LeadingKeys`
- CloudFormation outputs for deployed resource identifiers

The repository also includes Python/boto3 demonstrations for DynamoDB access and IAM policy simulation.

## Authorization Model

The authenticated identity receives a role through the Cognito Identity Pool.

The role permits:

- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`

Access is limited to the DynamoDB table created by the stack.

The policy condition requires the requested item's leading key to match the caller's Cognito identity.

Conceptually:

```text
Authenticated User A
        |
        v
Temporary AWS credentials
        |
        v
IAM authorization
        |
        +---- User A key → ALLOW
        |
        +---- User B key → DENY
```

The security boundary therefore exists at the authorization layer rather than relying solely on the application to decide which records a user may access.

## Why This Matters

Traditional application authorization can become difficult to maintain when access rules are implemented only inside application code.

Identity-aware IAM policies provide another enforcement layer.

This approach can help:

- Reduce unauthorized data access
- Limit the blast radius of compromised credentials
- Apply least-privilege authorization
- Make authorization decisions explicit
- Separate authentication from authorization
- Enforce data-access boundaries closer to the resource

## Infrastructure as Code

AWS CDK is used to define the infrastructure in Python.

CDK synthesizes the application into AWS CloudFormation resources.

Typical workflow:

```bash
make synth
make deploy
make simulate
make ddb-demo
make destroy
```

`cdk synth` can be used to inspect the generated CloudFormation before deployment.

`cdk destroy` removes the resources managed by the stack.

## Secure Development Practices

The repository includes development controls intended to reduce common security issues in the supporting Python code.

These include:

- Bandit security scanning
- Secret detection
- Code formatting and linting
- Pre-commit checks
- Dependency management
- CI validation
- CDK synthesis validation

No application credentials or AWS secrets are intended to be stored in source code.

## Validation

The intended security validation is to demonstrate that:

1. An authenticated identity can obtain temporary credentials.
2. The identity can access its permitted DynamoDB data.
3. The IAM policy restricts access to the identity's permitted partition.
4. A cross-user data-access attempt is denied.

The repository's policy-simulation and boto3 demonstration scripts support validation of the authorization model.

## Limitations

This is a focused identity and authorization demonstration rather than a complete production application.

It does not attempt to implement:

- Enterprise workforce identity federation
- Privileged access management
- Full customer identity lifecycle management
- Application-wide authorization policy management
- Enterprise SIEM integration
- Production disaster recovery
- Multi-region architecture
- Complete compliance implementation

Those capabilities would require additional architecture and operational controls.

## Key Lesson

Authentication establishes **who the user is**.

Authorization determines **what that identity is allowed to access**.

This project demonstrates how AWS-native identity, temporary credentials, IAM policy conditions, and resource-level authorization can work together to enforce a specific data-access boundary.

## Technologies

- Amazon Cognito
- Amazon Cognito Identity Pools
- AWS STS
- AWS IAM
- Amazon DynamoDB
- AWS CDK
- AWS CloudFormation
- Python
- boto3
