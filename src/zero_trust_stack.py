from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)


class IdentityScopedDataAccessStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        name_prefix = "identity-scoped-access"

        # DynamoDB table
        # userId is the partition key used for identity-scoped authorization.
        table = dynamodb.Table(
            self,
            "UserItems",
            table_name=f"{name_prefix}-user-items",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Cognito User Pool
        # Provides application-user authentication.
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"{name_prefix}-user-pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                username=True,
                email=True,
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # User Pool Client
        # Allows an application/user to authenticate against the User Pool.
        user_pool_client = user_pool.add_client(
            "UserPoolClient",
            user_pool_client_name=f"{name_prefix}-client",
            generate_secret=False,
        )

        # Cognito Identity Pool
        # Exchanges authenticated Cognito identities for temporary AWS
        # credentials through AWS STS.
        identity_pool = cognito.CfnIdentityPool(
            self,
            "IdentityPool",
            identity_pool_name=f"{name_prefix}-identity-pool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=user_pool_client.user_pool_client_id,
                    provider_name=user_pool.user_pool_provider_name,
                    server_side_token_check=True,
                )
            ],
        )

        # IAM role assumed only by authenticated identities from this
        # specific Cognito Identity Pool.
        auth_role = iam.Role(
            self,
            "AuthenticatedUserRole",
            role_name=f"{name_prefix}-authenticated-role",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description=(
                "Role assumed by authenticated Cognito identities "
                "for identity-scoped DynamoDB access"
            ),
        )

        # DynamoDB authorization policy
        #
        # The role can access only records whose leading partition key
        # matches the Cognito identity associated with the temporary
        # credentials.
        auth_policy = iam.Policy(
            self,
            "IdentityScopedDynamoDbPolicy",
            policy_name=f"{name_prefix}-dynamodb-policy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                    ],
                    resources=[table.table_arn],
                    conditions={
                        "ForAllValues:StringEquals": {
                            "dynamodb:LeadingKeys": [
                                "${cognito-identity.amazonaws.com:sub}"
                            ]
                        }
                    },
                )
            ],
        )

        auth_policy.attach_to_role(auth_role)

        # Associates the authenticated IAM role with the Identity Pool.
        cognito.CfnIdentityPoolRoleAttachment(
            self,
            "IdentityPoolRoleAttachment",
            identity_pool_id=identity_pool.ref,
            roles={
                "authenticated": auth_role.role_arn,
            },
        )

        # CloudFormation outputs
        cdk.CfnOutput(
            self,
            "UserPoolId",
            value=user_pool.user_pool_id,
        )

        cdk.CfnOutput(
            self,
            "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
        )

        cdk.CfnOutput(
            self,
            "IdentityPoolId",
            value=identity_pool.ref,
        )

        cdk.CfnOutput(
            self,
            "TableName",
            value=table.table_name,
        )

        cdk.CfnOutput(
            self,
            "AuthenticatedRoleArn",
            value=auth_role.role_arn,
        )
