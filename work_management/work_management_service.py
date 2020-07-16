from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from aws_cdk import core
import aws_cdk.aws_iam as iam


class WorkMgntService(core.Construct):
    def __init__(self, scope: core.Construct, id: str):
        super().__init__(scope, id)

        wallet_table = dynamodb.Table(self, "WalletDetailTest",
                                      table_name="WalletDetailTest",
                                      read_capacity=1,
                                      write_capacity=1,
                                      partition_key=dynamodb.Attribute(
                                          name="id",
                                          type=dynamodb.AttributeType.STRING
                                      ))
        transaction_table = dynamodb.Table(self, "TransactionDetailTest", table_name="TransactionDetailTest",
                                           read_capacity=1,
                                           write_capacity=1,
                                           partition_key=dynamodb.Attribute(
                                               name="walId",
                                               type=dynamodb.AttributeType.STRING),
                                           sort_key=dynamodb.Attribute(
                                               name="date",
                                               type=dynamodb.AttributeType.STRING)
                                           )

        transfer_handler = lambda_.Function(self, "TransferHandler",
                                            function_name="transfer",
                                            runtime=lambda_.Runtime.PYTHON_3_7,
                                            code=lambda_.Code.asset(
                                                "resources"),
                                            handler="transfer.handler",
                                            environment=dict(
                                                WALLET_TABLE=wallet_table.table_name,
                                                TRANSACTION_TABLE=transaction_table.table_name)
                                            )

        transaction_table.grant_read_write_data(transfer_handler)
        wallet_table.grant_read_write_data(transfer_handler)

        get_wallet_balance_handler = lambda_.Function(self, "getWalletBalanceHandler",
                                                      function_name="get-wallet-balance",
                                                      runtime=lambda_.Runtime.PYTHON_3_7,
                                                      code=lambda_.Code.asset(
                                                          "resources"),
                                                      handler="get_wallet_balance.handler",
                                                      environment=dict(
                                                          WALLET_TABLE=wallet_table.table_name)
                                                      )

        wallet_table.grant_read_data(get_wallet_balance_handler)

        manage_wallet_handler = lambda_.Function(self, "ManageWalletHandler",
                                                 function_name="manage-wallet",
                                                 runtime=lambda_.Runtime.PYTHON_3_7,
                                                 code=lambda_.Code.asset(
                                                     "resources"),
                                                 handler="manage_wallet.handler",
                                                 environment=dict(
                                                     WALLET_TABLE=wallet_table.table_name)
                                                 )

        wallet_table.grant_read_write_data(manage_wallet_handler)

        # work management code
        workmgnt_table = dynamodb.Table(self, "WorkManagement",  table_name="WorkManagement",
                                        read_capacity=1,
                                        write_capacity=1,
                                        partition_key=dynamodb.Attribute(
                                            name="workId",
                                            type=dynamodb.AttributeType.STRING
                                        ))

        gsi_workmgnt_table_by_acctid = workmgnt_table.add_global_secondary_index(
            partition_key=dynamodb.Attribute(
                name="accountId", type=dynamodb.AttributeType.STRING),
            #sort_key=dynamodb.Attribute(name="currentStatus", type=dynamodb.AttributeType.STRING),
            index_name="workmgnt_acctid-index",
            read_capacity=30,
            write_capacity=30,
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["orgId", "closedDate", "functionalDomain", "skills", "criticalWork", "biddingEndDateTime", "currentStatus"])

        gsi_workmgnt_table_by_delegateid = workmgnt_table.add_global_secondary_index(
            partition_key=dynamodb.Attribute(
                name='delegateAccountId', type=dynamodb.AttributeType.STRING),
            #sort_key=dynamodb.Attribute(name="currentStatus", type=dynamodb.AttributeType.STRING),
            index_name="workmgnt_delegateid-index",
            read_capacity=30,
            write_capacity=30,
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["orgId", "closedDate", "functionalDomain", "skills", "criticalWork", "biddingEndDateTime", "currentStatus"])

        workmgnt_allocation_table = dynamodb.Table(self, "WorkManagementAllocation",  table_name="WorkManagementAllocation",
                                                   read_capacity=1,
                                                   write_capacity=1,
                                                   partition_key=dynamodb.Attribute(
                                                       name="accountId", type=dynamodb.AttributeType.STRING),
                                                   sort_key=dynamodb.Attribute(
                                                       name="workAcctStatus", type=dynamodb.AttributeType.STRING))

        create_handler = lambda_.Function(self, "WorkMngtCreateHandler",
                                          function_name="create-work",
                                          runtime=lambda_.Runtime.PYTHON_3_7,
                                          code=lambda_.Code.asset("resources"),
                                          handler="create.handler",
                                          environment=dict(
                                              WORKMGNT_TABLE=workmgnt_table.table_name)
                                          )

        workmgnt_table.grant_read_write_data(create_handler)

        create_handler.role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=['lambda:InvokeFunction'],
            resources=['*']
        ))

        delete_handler = lambda_.Function(self, "WorkMngtDeleteHandler",
                                          function_name="delete-work",
                                          runtime=lambda_.Runtime.PYTHON_3_7,
                                          code=lambda_.Code.asset("resources"),
                                          handler="delete.handler",
                                          environment=dict(
                                              WORKMGNT_TABLE=workmgnt_table.table_name)
                                          )

        workmgnt_table.grant_write_data(delete_handler)

        put_handler = lambda_.Function(self, "WorkMngtUpdateHandler",
                                       function_name="update-work",
                                       runtime=lambda_.Runtime.PYTHON_3_7,
                                       code=lambda_.Code.asset("resources"),
                                       handler="update.handler",
                                       environment=dict(
                                           WORKMGNT_TABLE=workmgnt_table.table_name)
                                       )

        workmgnt_table.grant_write_data(put_handler)

        get_handler = lambda_.Function(self, "WorkMngtGetHandler",
                                       function_name="get-work",
                                       runtime=lambda_.Runtime.PYTHON_3_7,
                                       code=lambda_.Code.asset("resources"),
                                       handler="get.handler",
                                       environment=dict(
                                           WORKMGNT_TABLE=workmgnt_table.table_name)
                                       )

        workmgnt_table.grant_read_data(get_handler)

        api = apigateway.RestApi(self, "WorkMgnt-api",
                                 rest_api_name="WorkMgnt Service",
                                 description="This service serves WorkMgnt.")

        manage_wallet_integration = apigateway.LambdaIntegration(manage_wallet_handler,
                                                                 request_templates={
                                                                     "application/json": '{ "statusCode": "200" }'})

        get_wallet_balance_integration = apigateway.LambdaIntegration(get_wallet_balance_handler,
                                                                      request_templates={
                                                                          "application/json": '{ "statusCode": "200" }'})
        transfer_integration = apigateway.LambdaIntegration(transfer_handler,
                                                            request_templates={
                                                                "application/json": '{ "statusCode": "200" }'})

        post_integration = apigateway.LambdaIntegration(create_handler,
                                                        request_templates={
                                                            "application/json": '{ "statusCode": "200" }'})
        delete_integration = apigateway.LambdaIntegration(delete_handler,
                                                          request_templates={
                                                              "application/json": '{ "statusCode": "200" }'})
        put_integration = apigateway.LambdaIntegration(put_handler,
                                                       request_templates={
                                                           "application/json": '{ "statusCode": "200" }'})
        get_integration = apigateway.LambdaIntegration(get_handler,
                                                       request_templates={
                                                           "application/json": '{ "statusCode": "200" }'})

        api.root.add_method("POST", post_integration)  # POST /
        api.root.add_method("PUT", transfer_integration)  # PUT /{id}
        api.root.add_resource("workmgnt").add_resource(
            "{id}").add_method("PUT", put_integration)  # PUT /{id}

        api.root.add_resource("managewallet").add_method(
            "PUT", manage_wallet_integration)

        api.root.add_resource("wallet").add_method(
            "PUT", get_wallet_balance_integration)

        work_resource = api.root.add_resource("{id}")

        # api.root.{accountId}.{orgId}.{status}.add_method("GET", get_integration  )
        api.root.add_method("GET", get_integration)
        work_resource.add_method("GET", get_integration)

        work_resource.add_method("DELETE", delete_integration)  # DELETE /{id}
