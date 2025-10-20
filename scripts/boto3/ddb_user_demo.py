from botocore.config import Config
# scripts/boto3/ddb_user_demo.py
# Writes & reads a single 'userId' item.
import os, uuid, json, boto3

region = os.getenv("AWS_REGION", os.getenv("CDK_DEFAULT_REGION", "us-east-1"))
table_name = os.getenv("TABLE_NAME", "wa-sec-01-user-items")
user_id = os.getenv("USER_ID", "demo-user-123")  # In real flow, derive from identity context

ddb = boto3.client("dynamodb", region_name=region, config=Config(retries={'max_attempts':5}, connect_timeout=3, read_timeout=5, user_agent_extra='wa-sec-01') )

item = {
    "userId": {"S": user_id},
    "settings": {"S": json.dumps({"theme":"dark","lang":"en"})},
    "nonce": {"S": str(uuid.uuid4())}
}

print(f"Putting item for userId={user_id} into {table_name}...")
ddb.put_item(TableName=table_name, Item=item)
print("OK. Reading it back...")
res = ddb.get_item(TableName=table_name, Key={"userId": {"S": user_id}})
print("Item:", res.get("Item"))