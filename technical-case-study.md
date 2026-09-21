# Technical Case Study — Identity-Scoped Data Access on AWS

## Architecture Problem

Authentication answers an important security question:

> Who is the user?

It does not, by itself, answer a second question:

> Which data should that identity be allowed to access?

An application can enforce this distinction entirely within application code, but that places significant trust in the application authorization layer.

This project explores an additional authorization boundary using AWS identity federation, temporary credentials, IAM policy conditions, and DynamoDB partition keys.

The security objective is:

> An authenticated identity should be able to access its own data while being denied access to data assigned to another identity.

## Security Requirements

The architecture was designed around several requirements:

- Users must authenticate before receiving access to AWS resources.
- Unauthenticated identities must not receive AWS credentials.
- Long-lived AWS credentials must not be embedded in the application.
- Authenticated identities should receive temporary credentials.
- The authenticated role should expose only required DynamoDB operations.
- Authorization should be constrained to the intended DynamoDB table.
- Data access should be restricted according to the authenticated identity.
- Cross-user access should be denied even when the caller is otherwise authenticated.
- Changes to identity trust and authorization policies should be reviewable as infrastructure code.

## Architecture

The implemented authorization path is:

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

Each component performs a different security function.

### Cognito User Pool

The User Pool provides user authentication.

Its responsibility is establishing the application user's identity.

Authentication alone does not grant unrestricted DynamoDB access.

### User Pool Client

The User Pool Client represents the application interaction with the User Pool and participates in the authentication flow.

It is configured without a client secret for this demonstration.

### Cognito Identity Pool

The Identity Pool connects the authenticated application identity to AWS authorization.

Unauthenticated identities are disabled.

The User Pool and User Pool Client are explicitly configured as an identity provider for the Identity Pool.

### AWS STS

AWS Security Token Service provides temporary credentials associated with the authenticated IAM role.

This avoids embedding long-lived AWS access credentials in application code.

The temporary credentials still require authorization. Possession of credentials does not imply unrestricted AWS access.

### IAM Role

The authenticated IAM role establishes the AWS authorization boundary.

Its trust relationship requires:

- The expected Cognito Identity Pool
- An authenticated Cognito context

The role therefore cannot be assumed through the Identity Pool's unauthenticated identity path.

### DynamoDB

The DynamoDB table uses `userId` as its partition key.

The authenticated role permits only:

- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`

The policy also uses `dynamodb:LeadingKeys` to constrain operations according to the caller's Cognito identity.

The authorization objective is therefore:

```text
Identity A
   |
   +---- A partition -> ALLOW
   |
   +---- B partition -> DENY
```

## Trust Boundaries

Several trust boundaries exist in the architecture.

### User to Authentication Service

User-supplied credentials cannot be treated as proof of identity until authentication succeeds.

### Authentication to AWS Federation

A successfully authenticated application identity must still be exchanged through the configured Identity Pool before receiving AWS credentials.

### Federation to IAM

Temporary credentials derive their permissions from the IAM role associated with the authenticated identity.

The IAM trust relationship controls who may assume that role.

### IAM to Data

The role's existence does not grant unrestricted DynamoDB access.

IAM evaluates the requested operation, target resource, and authorization condition before access is permitted.

This final boundary is particularly important because it places an authorization control closer to the protected data.

## Why Application Authentication Is Not Enough

A common authorization failure occurs when an application verifies that a user is authenticated but fails to verify ownership of the requested resource.

For example:

```text
GET /records/user-B
```

may originate from a completely legitimate authenticated User A.

Authentication succeeded.

Authorization should still fail.

This project demonstrates an architecture in which the AWS authorization layer participates in enforcing that distinction.

The application remains responsible for secure behavior, but it is not the only layer protecting the data boundary.

## Least-Privilege Decisions

The authenticated role does not receive broad DynamoDB permissions.

It does not require actions such as:

- `dynamodb:Scan`
- `dynamodb:DeleteTable`
- `dynamodb:CreateTable`
- DynamoDB administrative operations

The role receives only the data operations required by the demonstration.

The policy is also restricted to the specific DynamoDB table rather than all DynamoDB resources.

Finally, the `LeadingKeys` condition further constrains access within that table.

Least privilege therefore exists at multiple levels:

```text
AWS Service
   ↓
Specific Table
   ↓
Required Actions
   ↓
Identity-Scoped Data
```

## Control Failure Scenarios

The architecture depends on several controls working together.

### Overly Broad IAM Trust

If the IAM trust policy allowed identities from unintended Identity Pools or unauthenticated identities, unauthorized callers could potentially obtain the role.

### Removal of the LeadingKeys Condition

Removing the identity condition could turn a narrowly scoped role into one capable of accessing other users' records within the same table.

### Excessive DynamoDB Permissions

Adding operations such as `Scan` or broad administrative actions would increase the role's capabilities and potentially weaken the intended data boundary.

### Incorrect Identity Mapping

If the application uses an arbitrary user-supplied identifier rather than the identity established through the trusted authentication and federation path, the intended ownership model could be bypassed.

### Credential Compromise

Temporary credentials reduce the risks associated with long-lived keys but do not eliminate credential theft.

A stolen active session could still access resources authorized to that identity.

## Security Validation

Infrastructure deployment and security validation are separate activities.

A successful CloudFormation deployment proves that AWS accepted the resource configuration.

It does not prove that the authorization boundary behaves as intended.

The key validation scenarios are:

```text
Authenticated Identity A
        |
        +---- A data -> expected ALLOW
        |
        +---- B data -> expected DENY
```

The repository includes IAM policy simulation to examine authorization behavior and a boto3 script for basic DynamoDB interaction.

Policy simulation is useful for examining IAM decisions, but it should not be confused with a complete end-to-end runtime test.

Stronger validation would authenticate separate Cognito identities, obtain their temporary credentials, and execute both permitted and prohibited DynamoDB requests.

The denied request is particularly important because security controls should be validated through negative testing, not only successful access.

## Infrastructure and Change Governance

AWS CDK defines the identity, IAM, and DynamoDB resources in Python and synthesizes them into CloudFormation.

Changes can be reviewed with:

```bash
cdk diff
```

Identity and authorization changes deserve additional scrutiny during architecture review.

Examples include:

- Changing the IAM trust relationship
- Enabling unauthenticated identities
- Expanding DynamoDB actions
- Removing authorization conditions
- Changing role mappings
- Changing the partition-key strategy

These changes may appear small in infrastructure code while materially changing the security boundary.

## Secure Development Controls

The repository also includes supporting development controls:

- Ruff linting
- Black formatting validation
- Bandit static security analysis
- Secret detection
- Pre-commit validation
- CDK synthesis in CI

These controls protect the development process and infrastructure definitions.

They are supporting controls rather than the primary security architecture demonstrated by the project.

## Architecture Tradeoffs

### IAM Enforcement vs Application-Only Authorization

Adding IAM-based authorization provides another enforcement layer but also increases identity and policy complexity.

The organization must understand and maintain the relationship between application identity, Cognito identity, IAM conditions, and the data model.

### Fine-Grained Isolation vs Operational Complexity

Identity-scoped access can reduce blast radius, but increasingly granular policies and data partitions can become harder to operate at scale.

The appropriate authorization model depends on the application's access patterns and business requirements.

### Temporary Credentials vs Credential Management Simplicity

Federated temporary credentials reduce reliance on long-lived secrets but introduce dependencies on the identity and federation services.

Failure and recovery scenarios for those dependencies must be considered in production architecture.

## Production Considerations

This project demonstrates a focused authorization pattern rather than a complete production identity platform.

A production design would require additional decisions around:

- MFA
- Account recovery
- Identity lifecycle management
- Session duration
- Token handling
- Monitoring and alerting
- Audit-log retention
- Data encryption requirements
- Backup and recovery
- Deletion protection
- Environment isolation
- Privileged administration
- Incident response
- Availability and regional resilience

The demonstration also uses resource removal settings suitable for disposable infrastructure. Production data would require explicit retention and recovery decisions.

## Residual Risk

The architecture reduces the risk of one authenticated identity accessing another identity's data through the protected DynamoDB path.

It does not eliminate:

- Credential or session theft
- Compromise of an authorized user
- Application vulnerabilities
- Identity-provider misconfiguration
- Administrative misuse
- Authorization-policy drift
- Errors elsewhere in the application's data-access architecture

Those risks require additional preventive, detective, and operational controls.

## Architecture Decision

The central design decision is to avoid treating successful authentication as sufficient authorization.

Instead, the architecture carries trusted identity context into AWS authorization and uses IAM policy conditions to enforce an additional boundary at the data layer.

This creates defense in depth:

```text
Authenticate Identity
        ↓
Federate Identity
        ↓
Issue Temporary Credentials
        ↓
Authorize Required Actions
        ↓
Restrict Data Scope
```

## Key Takeaway

Identity security is not complete when a user successfully logs in.

The more important architecture question is what that authenticated identity can do next.

This project demonstrates how Cognito, AWS STS, IAM, and DynamoDB can work together so that authentication establishes identity while authorization constrains access to the data associated with that identity.
