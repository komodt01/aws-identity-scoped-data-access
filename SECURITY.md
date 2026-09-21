# Security Considerations

## Security Objective

The primary security objective of this project is to prevent one authenticated identity from accessing data assigned to another identity.

The intended authorization boundary is:

```text
Identity A -> Identity A data -> ALLOW
Identity A -> Identity B data -> DENY
```

This boundary depends on Cognito federation, temporary AWS credentials, IAM policy conditions, and the DynamoDB partition-key design working together.

## Authentication and Authorization

Authentication and authorization are treated as separate security decisions.

Amazon Cognito establishes the user identity.

The Cognito Identity Pool provides authenticated identities with access to temporary AWS credentials.

IAM determines which AWS actions those credentials may perform.

The DynamoDB `LeadingKeys` condition further restricts access according to the caller's Cognito identity.

Successful authentication does not imply unrestricted data access.

## IAM Trust Boundary

The authenticated IAM role is restricted to:

- The specific Cognito Identity Pool
- Authenticated identities
- The required DynamoDB operations
- The DynamoDB table created for this project
- Data matching the identity-scoped partition-key condition

Changes to the IAM trust policy or DynamoDB authorization condition should be treated as security-sensitive architecture changes.

## Temporary Credentials

The architecture uses identity federation and temporary AWS credentials rather than embedding long-lived AWS credentials in application code.

Repository code should not contain:

- AWS access keys
- Secret access keys
- Authentication tokens
- User passwords
- Production secrets

Local administrative access should use an approved AWS authentication mechanism such as IAM Identity Center or an assumed role.

## Data Access

The DynamoDB table uses `userId` as its partition key.

The authorization design depends on the relationship between that key and the authenticated Cognito identity.

Application-controlled identity values should not be treated as trustworthy substitutes for identity information established by the authentication and federation process.

## Validation

Deployment success does not prove that the authorization boundary works correctly.

Security validation should include both permitted and denied access scenarios.

At minimum:

```text
Authenticated Identity A
        |
        +---- Access A data -> expected ALLOW
        |
        +---- Access B data -> expected DENY
```

IAM policy simulation can help validate policy behavior, but runtime validation with actual authenticated identities provides stronger evidence.

## Secure Development Controls

The repository includes CI checks for:

- Python linting
- Formatting
- Bandit static security analysis
- Secret detection
- CDK synthesis

These controls help protect the supporting code and infrastructure definitions but do not replace runtime authorization testing.

## Sensitive Output

Validation scripts should avoid printing:

- Credentials
- Authentication tokens
- Complete sensitive records
- Secrets
- Personally identifiable information

Successful security validation should demonstrate the authorization decision without unnecessarily exposing protected data.

## Control Failure Scenarios

The intended security boundary could be weakened by:

- An overly broad IAM trust policy
- Allowing unauthenticated Identity Pool access
- Removing the DynamoDB `LeadingKeys` condition
- Expanding IAM permissions unnecessarily
- Incorrectly mapping application users to data partitions
- Treating user-supplied identifiers as trusted identity attributes
- Misconfiguring Cognito federation

These conditions should receive additional review during architecture and change management.

## Production Considerations

This repository demonstrates a focused authorization pattern rather than a complete production identity architecture.

A production implementation would require additional decisions around:

- Identity lifecycle management
- Account recovery
- MFA requirements
- Monitoring and alerting
- Audit-log retention
- Data encryption requirements
- Backup and recovery
- Data retention
- Environment separation
- Privileged administration
- Incident response

## Residual Risk

Identity-scoped IAM authorization reduces the risk of cross-user data access but does not eliminate all application or identity risk.

Compromised legitimate credentials may still allow access to the compromised identity's authorized data.

Additional controls would therefore be required to address credential theft, session abuse, application vulnerabilities, identity lifecycle failures, and other production threats.
