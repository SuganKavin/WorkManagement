from aws_cdk import (core,
                     aws_apigateway as apigateway,
                     aws_dynamodb as dynamodb,
                     aws_lambda as lambda_)


class WorkMgntService(core.Construct):
    def __init__(self, scope: core.Construct, id: str):
        super().__init__(scope, id)


        workmgnt_table = dynamodb.Table(self,"WorkManagement",  table_name="WorkManagement", partition_key=dynamodb.Attribute(
            name="id",
            type=dynamodb.AttributeType.STRING
        ))

        create_handler = lambda_.Function(self, "WorkMngtCreateHandler",
                                                 function_name="WorkMgntCreate",
                                                 runtime=lambda_.Runtime.PYTHON_3_7,
                                                 code=lambda_.Code.asset("resources"),
                                                 handler="create.handler",
                                                 environment=dict(
                                                     WORKMGNT_TABLE=workmgnt_table.table_name)
                                                 )

        workmgnt_table.grant_read_write_data(create_handler)

        api = apigateway.RestApi(self, "WorkMgnt-api",
                                 rest_api_name="WorkMgnt Service",
                                 description="This service serves WorkMgnt.")


        post_integration = apigateway.LambdaIntegration(create_handler,
                                                    request_templates={
                                                        "application/json": '{ "statusCode": "200" }'})

        api.root.add_method("POST", post_integration)  # POST /