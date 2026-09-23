# Architecture Considerations — Identity-Scoped Data Access

## Why These Considerations Matter

The implemented project focuses on one security problem: carrying an authenticated identity into AWS authorization so that data access can be constrained to the identity associated with that data.

That pattern is demonstrated with Cognito, temporary AWS credentials, IAM, `dynamodb:LeadingKeys`, and a DynamoDB partition key.

Moving the pattern into a production application raises a broader set of questions.

Rather than treating those questions as a checklist of additional security products, they can be grouped around four architecture decisions:

1. Who owns the identity?
2. What binds that identity to the data?
3. Who can change that relationship?
4. How do we continue proving that the isolation works?

These are production architecture considerations. They are not presented as capabilities implemented by this reference project.

---

## 1. Who Owns the Identity?

The authorization model begins with confidence in the identity entering the system.

Cognito provides the authentication and federation path in the reference implementation, but a production environment would need to define the complete lifecycle of that identity.

That includes questions such as:

- How is an identity created?
- What evidence is required before the identity is trusted?
- When is MFA required?
- How are lost credentials recovered?
- How are sessions managed?
- How quickly can compromised access be terminated?
- What happens when an account is disabled?
- How are duplicate or abandoned identities handled?

The data-access policy can be perfectly configured and still produce the wrong result if the identity entering the policy is wrong.

### Session and Credential Compromise

Temporary AWS credentials reduce dependence on long-lived AWS keys, but they do not eliminate session theft.

If an attacker obtains credentials associated with Identity A, the authorization layer may correctly allow access to Identity A's data because, from AWS's perspective, the request is arriving with Identity A's authority.

That means identity-scoped authorization limits the blast radius of a compromised identity; it does not prevent compromise of that identity's own authorized data.

Production architecture would need complementary controls around authentication strength, session lifetime, token handling, anomaly detection, credential protection, and incident response.

---

## 2. What Binds Identity to Data?

The security model depends on a relationship between the authenticated identity and the DynamoDB partition containing that identity's data.

In this implementation, that relationship is expressed through:

- Cognito identity context.
- `${cognito-identity.amazonaws.com:sub}`.
- `dynamodb:LeadingKeys`.
- The `userId` DynamoDB partition key.

Those pieces have to describe the same ownership model.

### Data Ownership Is Part of Authorization

A policy can evaluate correctly and still protect the wrong data if the underlying ownership information is incorrect.

For example, if a record is written under the wrong `userId`, IAM could enforce the `LeadingKeys` condition exactly as configured while the application still has a data-ownership problem.

Production design therefore needs to define where ownership originates and which component is authoritative for assigning it.

The application should not be able to convert an arbitrary caller-supplied identity value into trusted ownership merely because the caller is authenticated.

### When the Data Model Becomes More Complicated

The one-identity/one-partition model is useful for demonstrating the security pattern.

Real applications may require relationships such as:

- A user belonging to multiple organizations.
- Multiple users sharing a resource.
- Delegated access.
- Support personnel accessing customer records.
- Administrators performing controlled cross-user operations.
- Service identities processing data for many users.
- Records changing ownership.
- Users leaving an organization while business data must remain.

At that point, authorization may no longer be expressible as simply:

**identity ID = partition key**

That does not invalidate the demonstrated pattern.

It means the authorization model has to evolve with the business relationship represented by the data.

The architecture should avoid forcing a simple identity model onto a data model that no longer behaves that way.

---

## 3. Who Can Change the Relationship?

The data boundary is enforced at runtime, but its behavior is determined by configuration.

An administrator capable of changing the IAM role, Cognito federation configuration, Identity Pool mappings, DynamoDB policy condition, or data model can alter the effective authorization boundary.

That creates a different kind of privilege from normal application access.

### Control-Plane Authority

Production design should distinguish among people or workloads that can:

- Use the application.
- Deploy application code.
- Modify Cognito configuration.
- Modify IAM trust.
- Modify IAM permissions.
- Change Identity Pool role mappings.
- Change the DynamoDB data model.
- Administer production data.
- Disable or alter security monitoring.

These authorities do not necessarily belong to the same team or identity.

A normal application user should not be able to change the policy protecting their data.

Likewise, the ability to deploy application changes should not automatically imply unrestricted authority to weaken production IAM controls.

### Environment Separation

Development, testing, and production should not be treated as one authorization domain.

A production design would need to decide how identities, AWS accounts, roles, data, deployment authority, and administrative privileges are separated between environments.

This is particularly important for identity testing.

Test identities and test data should not require broad access to production identity or customer data simply because the same application architecture exists in both environments.

### Security-Sensitive Changes

Some infrastructure changes deserve more scrutiny than their size in a CDK diff might suggest.

For example:

```text
Remove LeadingKeys condition
