import json
import os
import uuid

import boto3
from botocore.config import Config

region = os.getenv(
    "AWS_REGION",
    os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
)

table_name = os.getenv(
    "TABLE_NAME",
    "identity-scoped-access-user-items",
)

user_id = os.getenv(
    "USER_ID",
    "demo-user-123",
)

config = Config(
    retries={"max_attempts": 5, "mode": "standard"},
    connect_timeout=3,
    read_timeout=5,
    user_agent_extra="identity-scoped-data-access",
)

ddb = boto3.client(
    "dynamodb",
    region_name=region,
    config=config,
)

item = {
    "userId": {"S": user_id},
    "settings": {
        "S": json.dumps(
            {
                "theme": "dark",
                "lang": "en",
            }
        )
    },
    "nonce": {"S": str(uuid.uuid4())},
}

print(f"Writing test item for userId={user_id} to {table_name}...")

ddb.put_item(
    TableName=table_name,
    Item=item,
)

print("Write successful. Reading item...")

response = ddb.get_item(
    TableName=table_name,
    Key={
        "userId": {"S": user_id},
    },
)

if "Item" in response:
    print("Read successful.")
else:
    print("Item was not returned.")
