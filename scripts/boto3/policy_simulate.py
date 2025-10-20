from botocore.config import Config
# scripts/boto3/policy_simulate.py
import boto3, os

account = os.getenv("AWS_ACCOUNT_ID", "123456789012")
role_name = os.getenv("ROLE_NAME", "wa-sec-01-cognito-auth-role")
region = os.getenv("AWS_REGION", os.getenv("CDK_DEFAULT_REGION","us-east-1"))
table_name = os.getenv("TABLE_NAME", "wa-sec-01-user-items")

dynamodb = boto3.client("dynamodb", region_name=region)
table_arn = f"arn:aws:dynamodb:{region}:{account}:table/{table_name}"

iam = boto3.client("iam", config=Config(retries={'max_attempts':5}, connect_timeout=3, read_timeout=5, user_agent_extra='wa-sec-01') )
resp = iam.simulate_principal_policy(
    PolicySourceArn=f"arn:aws:iam::{account}:role/{role_name}",
    ActionNames=["dynamodb:PutItem","dynamodb:GetItem","dynamodb:UpdateItem"],
    ResourceArns=[table_arn],
)
for r in resp["EvaluationResults"]:
    print(r["EvalActionName"], "=>", r["EvalDecision"])