#!/usr/bin/env python3

import os

import aws_cdk as cdk

from identity_scoped_data_access_stack import IdentityScopedDataAccessStack

app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION") or "us-east-1",
)

IdentityScopedDataAccessStack(
    app,
    "IdentityScopedDataAccessStack",
    env=env,
)

app.synth()
