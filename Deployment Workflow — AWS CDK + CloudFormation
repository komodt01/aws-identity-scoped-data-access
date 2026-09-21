# Deployment Workflow — Identity-Scoped Data Access

## Purpose

This document describes how the identity-scoped data access architecture is deployed using AWS CDK and AWS CloudFormation.

The deployment creates the infrastructure required for the following security path:

```text
Cognito User Pool
        |
        v
User Pool Client
        |
        v
Cognito Identity Pool
        |
        v
AWS STS temporary credentials
        |
        v
Authenticated IAM Role
        |
        v
Identity-Scoped DynamoDB Access
```

The primary security objective is to enforce authorization based on the authenticated identity rather than relying solely on application logic.

## 1. CDK Synthesis

The infrastructure is defined in Python using AWS CDK.

Before deployment:

```bash
cdk synth
```

CDK converts the Python infrastructure definition into an AWS CloudFormation template.

This provides an opportunity to inspect the resources, IAM policies, trust relationships, and other infrastructure changes before they are deployed.

## 2. CDK Bootstrap

AWS CDK requires the target AWS account and Region to be bootstrapped before the first deployment.

Example:

```bash
cdk bootstrap aws://<ACCOUNT_ID>/<REGION>
```

Do not store AWS account credentials in the repository.

Authentication to AWS should use an approved credential mechanism such as AWS IAM Identity Center, an assumed role, or another temporary-credential workflow.

## 3. Review Proposed Changes

Before modifying an existing deployment:

```bash
cdk diff
```

This displays the difference between the locally defined architecture and the currently deployed CloudFormation stack.

Security-sensitive changes should receive particular attention, including:

- IAM permissions
- IAM trust relationships
- Cognito configuration
- Identity Pool role mappings
- DynamoDB authorization conditions

A successful deployment does not by itself prove that the resulting authorization model is correct.

The security behavior must also be validated.

## 4. Deployment

Deploy the stack with:

```bash
cdk deploy
```

The stack provisions:

- Cognito User Pool
- Cognito User Pool Client
- Cognito Identity Pool
- IAM role for authenticated identities
- IAM trust relationship for Cognito federation
- Identity-scoped DynamoDB permissions
- DynamoDB table
- CloudFormation outputs

The deployed stack is:

```text
IdentityScopedDataAccessStack
```

## 5. Authentication and Authorization Flow

After deployment, the intended runtime flow is:

1. A user authenticates through the Cognito User Pool.
2. The authenticated identity is associated with the Cognito Identity Pool.
3. The Identity Pool provides a path to temporary AWS credentials.
4. AWS STS issues temporary credentials associated with the authenticated role.
5. IAM evaluates the requested DynamoDB operation.
6. The DynamoDB `LeadingKeys` condition limits access according to the Cognito identity.
7. Requests outside the permitted identity scope should be denied.

This separates two security decisions:

**Authentication**

Determines who the user is.

**Authorization**

Determines which data that identity may access.

## 6. Validation

Infrastructure deployment should be followed by security validation.

The important security assertion is not simply that DynamoDB can be accessed.

The authorization boundary should demonstrate:

```text
Identity A -> Identity A data -> ALLOW

Identity A -> Identity B data -> DENY
```

The repository includes supporting scripts for DynamoDB interaction and IAM policy simulation.

Policy simulation provides useful authorization-policy validation, but it is not equivalent to a complete runtime test using an authenticated Cognito identity.

## 7. Change Management

The normal infrastructure lifecycle is:

```bash
cdk synth
cdk diff
cdk deploy
```

Changes affecting identity or authorization deserve additional review because a syntactically valid policy can still create an unintended security exposure.

Examples include:

- Expanding permitted DynamoDB actions
- Removing identity conditions
- Broadening the IAM trust relationship
- Allowing unauthenticated identities
- Changing Identity Pool role mappings
- Changing the DynamoDB partition-key model

These are security architecture changes, not merely infrastructure changes.

## 8. Teardown

For this demonstration environment:

```bash
cdk destroy
```

The CDK stack uses removal settings appropriate for a disposable demonstration environment.

A production environment would require separate decisions regarding:

- Data retention
- Backup
- Recovery
- Deletion protection
- Change approval
- Environment separation

Production data should not inherit demonstration-oriented deletion behavior without an explicit architecture decision.

## Security Considerations

The architecture relies on several controls working together.

A failure or misconfiguration in any of the following could weaken the intended authorization boundary:

- User authentication
- User Pool configuration
- Identity Pool federation
- IAM role trust policy
- IAM permissions
- DynamoDB condition keys
- Application handling of identity information

For that reason, deployment success and security-control effectiveness should be treated as separate questions.

## Key Takeaway

Infrastructure as Code provides repeatability and change visibility.

It does not automatically guarantee secure authorization.

The security objective of this project is therefore not simply to deploy Cognito, IAM, and DynamoDB. It is to establish and validate an identity-based boundary that prevents one authenticated identity from accessing another identity's data.
