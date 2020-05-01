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

        workstatus_table = dynamodb.Table(self,"WorkMgntStatus",  table_name="WorkMgntStatus", partition_key=dynamodb.Attribute(
            name="id",
            type=dynamodb.AttributeType.STRING
        ))

        create_handler = lambda_.Function(self, "WorkMngtCreateHandler",
                                                 function_name="WorkMgntCreate",
                                                 runtime=lambda_.Runtime.PYTHON_3_7,
                                                 code=lambda_.Code.asset("resources"),
                                                 handler="create.handler",
                                                 environment=dict(
                                                     WORKMGNT_TABLE=workmgnt_table.table_name,
                                                     WORKMGNTSTATUS_TABLE=workstatus_table.table_name)
                                                 )

        workmgnt_table.grant_read_write_data(create_handler)
        workstatus_table.grant_read_write_data(create_handler)

        get_handler = lambda_.Function(self, "WorkMngtGetHandler",
                                       function_name="WorkMgntGet",
                                       runtime=lambda_.Runtime.PYTHON_3_7,
                                       code=lambda_.Code.asset("resources"),
                                       handler="get.handler",
                                       environment=dict(
                                           WORKMGNT_TABLE=workmgnt_table.table_name)
                                       )

        workmgnt_table.grant_read_data(get_handler)

        put_handler = lambda_.Function(self, "WorkMngtUpdateHandler",
                                       function_name="WorkMgntUpdate",
                                       runtime=lambda_.Runtime.PYTHON_3_7,
                                       code=lambda_.Code.asset("resources"),
                                       handler="update.handler",
                                       environment=dict(
                                           WORKMGNT_TABLE=workmgnt_table.table_name,
                                           WORKMGNTSTATUS_TABLE=workstatus_table.table_name)
                                       )

        workmgnt_table.grant_write_data(put_handler)
        workstatus_table.grant_write_data(put_handler)

        delete_handler = lambda_.Function(self, "WorkMngtDeleteHandler",
                                          function_name="WorkMgntDelete",
                                          runtime=lambda_.Runtime.PYTHON_3_7,
                                          code=lambda_.Code.asset("resources"),
                                          handler="delete.handler",
                                          environment=dict(
                                              WORKMGNT_TABLE=workmgnt_table.table_name)
                                          )

        workmgnt_table.grant_write_data(delete_handler)

        workmgnt_table.grant_read_write_data(create_handler)


        api = apigateway.RestApi(self, "WorkMgnt-api",
                                 rest_api_name="WorkMgnt Service",
                                 description="This service serves WorkMgnt.")


        post_integration = apigateway.LambdaIntegration(create_handler,
                                                    request_templates={
                                                        "application/json": '{ "statusCode": "200" }'})

        get_integration = apigateway.LambdaIntegration(get_handler,
                                                               request_templates={
                                                                   "application/json": '{ "statusCode": "200" }'})

        put_integration = apigateway.LambdaIntegration(put_handler,
                                                               request_templates={
                                                                   "application/json": '{ "statusCode": "200" }'})

        delete_integration = apigateway.LambdaIntegration(delete_handler,
                                                                  request_templates={
                                                                      "application/json": '{ "statusCode": "200" }'})

        api.root.add_method("POST", post_integration)  # POST /

        resource = api.root.add_resource("{id}")

        resource.add_method("PUT", put_integration)  # PUT /{id}

        resource.add_method("GET", get_integration)  # GET /{id}

        resource.add_method("DELETE", delete_integration)  # DELETE /{id}