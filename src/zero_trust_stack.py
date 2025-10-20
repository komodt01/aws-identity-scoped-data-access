from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_cognito as cognito,
    aws_iam as iam,
)

class ZeroTrustStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        name_prefix = "wa-sec-01"

        # DynamoDB table with PK userId
        table = dynamodb.Table(
            self, "UserItems",
            table_name=f"{name_prefix}-user-items",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Cognito User Pool
        user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name=f"{name_prefix}-user-pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Identity Pool (authenticated only)
        identity_pool = cognito.CfnIdentityPool(
            self, "IdentityPool",
            identity_pool_name=f"{name_prefix}-identity-pool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[],
        )

        # Role for authenticated identities
        auth_role = iam.Role(
            self, "AuthRole",
            role_name=f"{name_prefix}-cognito-auth-role",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": identity_pool.ref
                    },
                    # Optionally enforce authenticated context:
                    # "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "authenticated"}
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description="Role assumed by Cognito authenticated identities"
        )

        # Policy: only allow access to items whose PK matches the caller's Cognito identity sub
        auth_policy = iam.Policy(
            self, "DdbPerUserPolicy",
            policy_name=f"{name_prefix}-ddb-per-user",
            statements=[
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem","dynamodb:GetItem","dynamodb:UpdateItem"],
                    resources=[table.table_arn],
                    conditions={
                        "ForAllValues:StringEquals": {
                            "dynamodb:LeadingKeys": ["${cognito-identity.amazonaws.com:sub}"]
                        }
                    }
                )
            ]
        )
        auth_policy.attach_to_role(auth_role)

        # Attach role to Identity Pool (authenticated)
        cognito.CfnIdentityPoolRoleAttachment(
            self, "IdentityPoolRoleAttachment",
            identity_pool_id=identity_pool.ref,
            roles={
                "authenticated": auth_role.role_arn
            }
        )

        # Outputs
        cdk.CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        cdk.CfnOutput(self, "IdentityPoolId", value=identity_pool.ref)
        cdk.CfnOutput(self, "TableName", value=table.table_name)
        cdk.CfnOutput(self, "AuthRoleArn", value=auth_role.role_arn)