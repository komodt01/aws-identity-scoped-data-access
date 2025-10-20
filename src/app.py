#!/usr/bin/env python3
import os
import aws_cdk as cdk
from zero_trust_stack import ZeroTrustStack

app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION") or "us-east-1",
)

ZeroTrustStack(app, "Sec01ZeroTrustStack", env=env)

app.synth()