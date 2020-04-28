#!/usr/bin/env python3

from aws_cdk import core

from work_management.work_management_stack import WorkManagementStack


app = core.App()
WorkManagementStack(app, "work-management")

app.synth()
