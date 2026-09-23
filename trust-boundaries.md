# Trust Boundaries — AWS Identity-Scoped Data Access

## Purpose

This document identifies the major trust and authorization boundaries in the AWS Identity-Scoped Data Access architecture.

The reference implementation uses Amazon Cognito, Cognito Identity Pools, AWS STS, IAM, and DynamoDB to establish an authorization path in which an authenticated identity is intended to access only the DynamoDB data associated with that identity.

The core security objective is:

**Identity A → Identity A Data → ALLOW**

**Identity A → Identity B Data → DENY**

The architecture does not treat successful authentication as sufficient authorization.

Instead, access crosses multiple boundaries:

**User → Authentication → Federation → Temporary AWS Credentials → IAM Authorization → Identity-Scoped Data**

Each transition represents a separate security decision or trust relationship.

The repository demonstrates the architecture and supporting policy controls, but the complete end-to-end Cognito runtime test using separate identities has not yet been implemented.

---

## 1. User → Cognito User Pool

The first trust boundary exists between an unauthenticated application user and the Cognito User Pool.

Before authentication succeeds, user-supplied credentials and identity claims cannot be treated as trusted proof of identity.

### Implemented Boundary

The Cognito User Pool provides application-user authentication.

The User Pool establishes an authenticated application identity before the architecture proceeds to AWS federation.

### Security Significance

Authentication answers:

**Who is the user?**

It does not answer:

**Which AWS resources or application data may that user access?**

Successful User Pool authentication therefore does not eliminate the authorization boundaries that follow.

---

## 2. User Pool → User Pool Client

The User Pool Client represents the application interaction with the Cognito User Pool.

The client participates in the authentication flow but does not independently define the user's DynamoDB authorization.

### Implemented Boundary

The reference implementation creates a User Pool Client without a client secret.

The User Pool and User Pool Client are configured as the identity provider used by the Cognito Identity Pool.

### Security Significance

Application authentication configuration is part of the identity trust chain.

Changes to the User Pool Client or authentication configuration can affect which identities are able to enter the federation path.

Production architecture would therefore treat identity-provider and client configuration as security-sensitive configuration.

---

## 3. Authenticated Application Identity → Cognito Identity Pool

Authentication to the User Pool does not directly provide AWS credentials.

The authenticated application identity must cross another boundary through the Cognito Identity Pool.

### Implemented Boundary

The Identity Pool is configured to use the Cognito User Pool and User Pool Client as an identity provider.

Unauthenticated Identity Pool access is disabled.

The Identity Pool therefore provides the bridge between authenticated application identity and AWS authorization.

### Security Significance

This boundary separates:

**Application authentication**

from

**AWS credential federation**

An authenticated application identity does not automatically become an unrestricted AWS identity.

---

## 4. Cognito Identity Pool → AWS STS Temporary Credentials

The next boundary converts authenticated identity context into temporary AWS credentials.

AWS STS provides temporary credentials associated with the authenticated IAM role.

### Implemented Boundary

The architecture uses temporary AWS credentials rather than embedding long-lived AWS access keys in application code.

### Security Significance

Temporary credentials reduce persistence compared with long-lived access keys.

They do not eliminate credential risk.

A stolen active credential or session may still perform actions authorized to that identity until the credential expires or otherwise becomes unusable.

The architecture therefore distinguishes:

**Credential lifetime**

from

**Credential authorization**

Temporary does not mean unrestricted, and temporary does not mean harmless if compromised.

---

## 5. Cognito Federation → Authenticated IAM Role

The IAM role represents a critical authorization boundary.

Receiving authenticated identity context does not by itself authorize assumption of any AWS role.

### Implemented Enforcement

The role trust relationship requires:

- The expected Cognito Identity Pool.
- Authenticated Cognito context.
- Role assumption through `sts:AssumeRoleWithWebIdentity`.

Unauthenticated Identity Pool access is disabled.

### Security Significance

The trust relationship determines which federated identities may obtain the permissions associated with the role.

Broadening this relationship could materially change the architecture even if the DynamoDB permission policy remained unchanged.

Changes to the trust relationship should therefore be treated as security architecture changes rather than routine infrastructure modifications.

---

## 6. Temporary AWS Credentials → IAM Authorization

Possession of temporary AWS credentials does not provide unrestricted AWS access.

The credentials receive the permissions associated with the authenticated IAM role.

### Implemented Enforcement

The role permits only:

- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`

The permissions apply only to the DynamoDB table created by the stack.

### Security Significance

The authorization boundary constrains access across several dimensions:

**AWS Service → Specific Resource → Permitted Actions → Permitted Data**

The role does not receive broad DynamoDB administrative permissions.

This limits the capabilities available if an authenticated credential is misused.

---

## 7. IAM Role → DynamoDB Data Partition

This is the primary data-authorization boundary demonstrated by the architecture.

An authenticated identity should not be able to access every record simply because it has permission to use DynamoDB.

### Implemented Enforcement

The DynamoDB table uses `userId` as its partition key.

The IAM policy applies:

`dynamodb:LeadingKeys`

using:

`${cognito-identity.amazonaws.com:sub}`

The intended authorization relationship is:

**Authenticated Cognito Identity → Matching DynamoDB Partition**

### Security Objective

The architecture is designed to produce:

**Identity A → A Data → ALLOW**

and:

**Identity A → B Data → DENY**

This places an authorization control close to the protected data rather than relying exclusively on application authorization logic.

### Validation Boundary

The policy and infrastructure supporting this architecture are implemented.

However, the repository does not currently demonstrate the complete runtime test using separate authenticated Cognito identities.

The architecture should therefore be described as implementing the identity-scoped authorization mechanism without claiming that end-to-end cross-identity isolation has been fully runtime validated.

---

## 8. Trusted Identity Context → Application-Supplied Identity Values

One of the most important trust boundaries exists between identity information established through the trusted authentication/federation path and identifiers supplied by application users.

An application request may contain an identifier such as:

`userId`

That value should not automatically be treated as proof of identity or ownership.

### Security Significance

An authenticated Identity A could attempt to request:

**userId = Identity B**

The fact that the request came from an authenticated user does not make the requested identifier trustworthy.

The architecture therefore relies on identity context established through Cognito and AWS authorization rather than trusting arbitrary application-supplied ownership claims.

This distinction helps reduce authorization failures in which authentication succeeds but object ownership is not independently enforced.

---

## 9. Application Authorization → AWS Authorization

Application logic and AWS IAM represent separate authorization layers.

The application remains responsible for secure behavior.

IAM provides an additional enforcement point.

### Security Significance

Application authorization could contain a defect that incorrectly requests another user's data.

The IAM condition is intended to prevent that application-layer mistake from automatically becoming authorized DynamoDB access.

This creates defense in depth:

**Application Authorization**

plus

**AWS Authorization**

The AWS control does not eliminate the need for secure application authorization, and application authorization should not be treated as a substitute for the AWS data-access boundary.

---

## 10. Normal Application Identity → Administrative Authority

The authenticated application role is intended for application data access.

Administrative authority represents a different trust level.

### Implemented Boundary

The demonstrated authenticated role does not receive DynamoDB administrative permissions such as:

- Table creation.
- Table deletion.
- Broad administrative operations.

### Production Considerations

A production architecture should distinguish among:

- Application users.
- Application workloads.
- Cloud administrators.
- Identity administrators.
- Security administrators.
- Data administrators.
- Break-glass administrators.

A normal application identity should not be able to modify the controls governing its own authorization.

---

## 11. Authorization Policy → Security Administrator

The IAM trust relationship, IAM permission policy, Identity Pool role mapping, and DynamoDB authorization condition determine the effective data-access boundary.

These controls are therefore security-sensitive assets.

### Security Significance

An attacker may not need to bypass the `LeadingKeys` condition directly if they can instead modify the policy that contains it.

Security-sensitive changes include:

- Broadening the IAM trust relationship.
- Enabling unauthenticated identities.
- Removing `dynamodb:LeadingKeys`.
- Expanding permitted DynamoDB actions.
- Changing Identity Pool role mappings.
- Changing the DynamoDB partition-key model.
- Associating a broader IAM role with authenticated identities.

Production architecture should govern who can make these changes and how those changes are approved, detected, and audited.

---

## 12. Infrastructure Definition → Deployed Security Control

AWS CDK defines the intended identity and authorization architecture.

CDK synthesizes that definition into CloudFormation.

A boundary therefore exists between:

**Architecture expressed as code**

and

**Security behavior of the deployed environment**

### Security Significance

Successful:

`cdk synth`

demonstrates that the infrastructure definition can be synthesized.

Successful:

`cdk deploy`

demonstrates that AWS accepted and deployed the configuration.

Neither alone proves that the runtime authorization boundary behaves correctly.

Security validation must independently test the resulting behavior.

---

## 13. Positive Access → Negative Authorization Testing

A successful request demonstrates only that some access is permitted.

It does not prove that prohibited access is denied.

### Required Security Assertion

The meaningful authorization test is:

**Identity A → A Data → expected ALLOW**

followed by:

**Identity A → B Data → expected DENY**

The denied request is essential evidence because the security objective is isolation, not simply successful DynamoDB connectivity.

### Current Project State

The repository includes:

- IAM policy simulation.
- Basic DynamoDB interaction.
- Infrastructure validation through CDK synthesis.

The complete Cognito-based A/B runtime authorization test is not currently implemented.

This remains an explicit validation boundary of the project.

---

## 14. Development Identity → Deployment Authority

The repository defines security-sensitive infrastructure.

The identity capable of modifying the repository is not necessarily the same identity that should be authorized to deploy changes into a production AWS environment.

### Production Considerations

Production architecture should determine:

- Who may change infrastructure definitions.
- Who may approve security-sensitive changes.
- Which workload or identity performs deployment.
- Which AWS accounts and environments that deployment identity may modify.
- Whether IAM and identity changes require additional approval.
- How deployment activity is logged.

Source control authority and cloud administrative authority should not automatically be equivalent.

---

## 15. Development Environment → Production Environment

The reference implementation uses settings appropriate for disposable demonstration infrastructure.

Production represents a different security and operational boundary.

### Current Demonstration

The DynamoDB table and Cognito resources use removal behavior appropriate for a disposable environment.

### Production Considerations

Production architecture would require explicit decisions regarding:

- Environment isolation.
- Separate AWS accounts where appropriate.
- Data retention.
- Backup.
- Recovery.
- Deletion protection.
- Change approval.
- Administrative access.
- Monitoring.
- Incident response.

Demonstration-oriented lifecycle settings should not automatically cross into production.

---

## Failure and Bypass Paths

Trust-boundary analysis should consider how the authorization model could fail even when the infrastructure remains technically operational.

### Compromised User Identity

An attacker controlling a legitimate identity may access data authorized to that identity.

Identity-scoped authorization limits cross-user access but does not protect the compromised user's own authorized data.

### Stolen Temporary Credentials

Temporary credentials reduce long-term persistence but may still be useful to an attacker during their active lifetime.

### Overly Broad IAM Trust

A broader trust relationship could allow unintended identities to obtain the authenticated role.

### Unauthenticated Identity Access

Enabling unauthenticated Identity Pool identities could introduce an authorization path that the current architecture intentionally disables.

### Removed Identity Condition

Removing `dynamodb:LeadingKeys` could allow the role to access records outside the intended identity partition.

### Excessive DynamoDB Permissions

Adding broad operations could weaken the data-access boundary or increase the impact of credential compromise.

### Incorrect Identity-to-Data Mapping

If DynamoDB records are associated with an incorrect identity value, IAM may correctly enforce a policy against an incorrect ownership model.

Authorization therefore depends on both policy correctness and data-model correctness.

### Application-Supplied Identity Trust

If application logic treats a caller-supplied `userId` as trusted ownership information, the application could create an authorization weakness outside the intended identity path.

### Identity or Federation Misconfiguration

Changes to User Pool, Identity Pool, provider, role mapping, or federation configuration could alter which identity reaches the AWS authorization layer.

### Authorization-Policy Drift

A secure initial policy can become weaker over time through infrastructure changes.

Production environments should detect and govern changes to identity and authorization controls.

---

## Implemented vs. Production Trust Boundaries

### Demonstrated by the Reference Implementation

The project implements:

- Cognito User Pool authentication infrastructure.
- User Pool Client.
- Cognito Identity Pool federation.
- Disabled unauthenticated Identity Pool access.
- Temporary AWS credential architecture.
- IAM trust restricted to the expected Identity Pool and authenticated context.
- DynamoDB permissions restricted to required data operations.
- Permissions restricted to the specific DynamoDB table.
- `dynamodb:LeadingKeys` identity condition.
- DynamoDB partitioning using `userId`.
- Identity Pool role attachment.
- Infrastructure definition through AWS CDK.
- IAM policy simulation support.
- Secure-development validation.

### Not Claimed as Fully Implemented or Validated

The project does not claim:

- Complete end-to-end Cognito A/B runtime isolation testing.
- Enterprise MFA architecture.
- Complete identity lifecycle management.
- Enterprise session-management controls.
- Centralized security monitoring.
- Production backup and recovery.
- Production data-retention controls.
- Production environment isolation.
- Enterprise privileged-administration controls.
- Full incident-response integration.
- Multi-region identity or data resilience.

These require additional architecture and validation beyond the reference implementation.

---

## Core Architecture Principle

Identity security should not stop after authentication.

The complete authorization path is:

**Authenticate the User → Federate the Identity → Issue Temporary Credentials → Restrict the AWS Role → Authorize the Required Operation → Restrict the Data Scope → Validate Both Allowed and Denied Behavior**

Each boundary should constrain the authority inherited from the boundary before it.

The central principle is:

**Authentication establishes who the identity is. Authorization determines what that identity is allowed to do, and the protected data layer should not rely solely on the application to enforce that distinction.**
