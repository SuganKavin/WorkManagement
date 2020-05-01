import json
import logging
import os
import boto3
import decimal
from botocore.exceptions import ClientError
from datetime import datetime

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    data = json.loads(event['body'])

    id  = event['pathParameters']['id']

    if not id:
        logging.error("Validation Failed. Missing id")
        raise Exception("Couldn't create the workid.")


    table = dynamodb.Table(os.environ['WORKMGNT_TABLE'])
    status_table = dynamodb.Table(os.environ['WORKMGNTSTATUS_TABLE'])


    expressionAttributeValues = {}
    updateExpression ='SET '

    for k, v in data.items():
        expressionAttributeValues[':%s'%(k)] =v
        if isinstance(v,list):
            updateExpression += "%s=list_append(%s,:%s),"%(k,k,k)
        else:
            updateExpression +=  '%s=:%s,'%(k,k)

    try:
        # update the account in the database
        result = table.update_item(
            Key={
                'id': event['pathParameters']['id']
            },
            ExpressionAttributeValues=expressionAttributeValues,
            UpdateExpression=updateExpression[:-1],
            ReturnValues='ALL_NEW',
        )

        replace_decimals(result)

        work_status_date =datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        status_result = status_table.update_item(
            Key={
                'id': event['pathParameters']['id']
            },
            ExpressionAttributeValues={
                ':status': data['status1'],
                ':statusDate': work_status_date,
                ':statusTransition':  [
                    {
                        "status":data['status1'],
                        "statusDate": work_status_date
                    }
                ]
            },
            UpdateExpression='SET status1 = :status, statusDate = :statusDate, statusTransition =list_append(statusTransition,:statusTransition)',
            ReturnValues='ALL_NEW',
        )


        # create a response
        response = {
            "statusCode": 200,
            "body": json.dumps(result['Attributes'])
        }
    except ClientError as ex:
        response = {
            "statusCode": 400,
            #"body": json.dumps(expression_attribute_values[:-1])
            "body": json.dumps(ex.response['Error']['Message'])
        }

    return response

def replace_decimals(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = replace_decimals(v)
        return obj
    elif isinstance(obj, set):
        return set(replace_decimals(i) for i in obj)
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj