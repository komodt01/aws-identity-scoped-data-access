# Trust Boundaries — Identity-Scoped Data Access

## The Security Question

This project started with a fairly simple question:

**After a user authenticates, what prevents that user from accessing somebody else's data?**

Authentication alone does not answer that question.

The architecture uses Cognito, temporary AWS credentials, IAM, and the DynamoDB data model to carry an authenticated identity toward a data-level authorization decision.

The intended result is:

**Identity A → A's data → ALLOW**

**Identity A → B's data → DENY**

That creates an authorization path with several places where trust changes.

---

## Following the Identity

### 1. From User to Authenticated Identity

The first change in trust occurs at the Cognito User Pool.

Before authentication, information supplied by the user cannot be treated as proof of identity. After successful authentication, Cognito provides an established application identity.

That is important, but it is only the beginning of the security decision.

A valid login means:

**This identity has authenticated.**

It does not mean:

**This identity may access every application record.**

That distinction drives the rest of the architecture.

---

### 2. From Application Identity to AWS Identity

The Cognito Identity Pool connects the authenticated application identity to AWS.

Unauthenticated identities are disabled in the implementation.

The Identity Pool then provides the federation path through which temporary AWS credentials can be obtained.

This is a separate trust decision from User Pool authentication.

The application user has crossed from:

**authenticated application identity**

to:

**identity capable of receiving AWS authorization**

The authenticated IAM role reinforces that boundary by restricting its trust relationship to the expected Identity Pool and authenticated context.

Broadening that trust relationship would change who can enter the AWS authorization path.

---

### 3. From Temporary Credentials to Permitted AWS Actions

Temporary credentials do not mean broad AWS access.

The authenticated role permits only:

- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`

and only against the DynamoDB table created for this project.

The role therefore narrows authority before the request reaches the data itself.

The progression is:

**Authenticated Identity → Temporary Credentials → Specific AWS Service → Specific Table → Required Operations**

This also limits the usefulness of the credentials compared with granting broad DynamoDB permissions.

Temporary credentials still need protection. If valid credentials are stolen, an attacker may be able to perform whatever actions that identity is currently authorized to perform.

Short-lived credentials reduce persistence; they do not eliminate credential compromise.

---

## Where the Data Boundary Actually Appears

The most important boundary in this project is inside the DynamoDB access model.

The table uses `userId` as the partition key.

The IAM policy applies `dynamodb:LeadingKeys` using:

`${cognito-identity.amazonaws.com:sub}`

The intention is to bind the AWS identity to the corresponding data partition.

That means authorization is not supposed to stop at:

**Can this identity call DynamoDB?**

It continues to:

**Which DynamoDB records may this identity operate on?**

This is the core security value of the architecture.

---

## Trusted Identity vs. Requested Identity

There is another boundary that is easy to miss.

An application request can contain a value identifying the record or user being requested.

That value came from the application side of the boundary.

It is not automatically proof of ownership.

For example, an authenticated Identity A could attempt to request data associated with Identity B.

Authentication has still succeeded.

The request should still fail.

The authorization design therefore depends on identity established through the Cognito and AWS federation path rather than treating a caller-supplied `userId` as proof that the caller owns that data.

This is why the relationship between identity and the DynamoDB partition key matters as much as the authentication mechanism itself.

---

## Two Enforcement Layers

The application still has responsibility for authorization.

The AWS layer does not replace that responsibility.

Instead, the design creates two opportunities to stop an invalid request:

**Application authorization**

and

**AWS IAM/data authorization**

If application logic accidentally requests another user's partition, the IAM condition is intended to provide another enforcement point before DynamoDB permits the operation.

That is the defense-in-depth objective of the project.

---

## Who Can Change the Boundary?

The authorization model depends on configuration as much as runtime authentication.

Several changes could materially alter the security boundary:

- Broadening the authenticated IAM role's trust relationship.
- Enabling unauthenticated Identity Pool access.
- Removing `dynamodb:LeadingKeys`.
- Expanding DynamoDB permissions.
- Changing Identity Pool role mappings.
- Changing the partition-key strategy.
- Trusting an application-provided identity value instead of established identity context.

Someone able to make those changes can affect the effective authorization model.

In a production environment, administration of identity configuration and authorization policy would therefore require its own access controls, review, logging, and change governance.

The identity consuming the application should not have authority to redefine the policy protecting its own data access.

---

## Code Is Not the Same as Enforcement

The architecture is defined using AWS CDK and deployed through CloudFormation.

That gives the project repeatability and makes security-sensitive changes reviewable.

It does not prove the security behavior.

There are three different questions:

**Can the infrastructure synthesize?**

**Can the infrastructure deploy?**

**Does the deployed authorization boundary actually prevent cross-identity access?**

Those are not equivalent.

The first two concern infrastructure.

The third concerns security behavior.

---

## The Test That Matters

The strongest validation for this architecture is not simply demonstrating that an authenticated user can read DynamoDB.

The meaningful test is:

```text
Identity A
   |
   +---- A data → ALLOW
   |
   +---- B data → DENY
