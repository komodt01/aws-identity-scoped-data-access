import os

import boto3
from botocore.config import Config


region = os.getenv(
    "AWS_REGION",
    os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
)

account_id = os.getenv("AWS_ACCOUNT_ID")

role_name = os.getenv(
    "ROLE_NAME",
    "identity-scoped-access-authenticated-role",
)

table_name = os.getenv(
    "TABLE_NAME",
    "identity-scoped-access-user-items",
)

identity_id = os.getenv(
    "IDENTITY_ID",
    "us-east-1:example-identity-id",
)

if not account_id:
    raise ValueError("AWS_ACCOUNT_ID environment variable must be set.")

table_arn = f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name}"

config = Config(
    retries={"max_attempts": 5, "mode": "standard"},
    connect_timeout=3,
    read_timeout=5,
    user_agent_extra="identity-scoped-data-access",
)

iam = boto3.client(
    "iam",
    region_name=region,
    config=config,
)

role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

response = iam.simulate_principal_policy(
    PolicySourceArn=role_arn,
    ActionNames=[
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
    ],
    ResourceArns=[table_arn],
    ContextEntries=[
        {
            "ContextKeyName": "dynamodb:LeadingKeys",
            "ContextKeyValues": [identity_id],
            "ContextKeyType": "stringList",
        },
        {
            "ContextKeyName": "cognito-identity.amazonaws.com:sub",
            "ContextKeyValues": [identity_id],
            "ContextKeyType": "string",
        },
    ],
)

print(f"Policy simulation for identity {identity_id}")

for result in response["EvaluationResults"]:
    print(f"{result['EvalActionName']} => {result['EvalDecision']}")
