import json
import logging
import os
import uuid
import boto3

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

    expression_attribute_values = "SET "

    for k, v in data.items():

        if k=="travelIndicator" or k=="criticalIndicator" or k=="internAllowedIndicator":
            expression_attribute_values += "%s= bool(%s),"%(k,v)
        elif k=="estimatedEffort" or k=="rewardUnits" :
            expression_attribute_values += "%s= %s,"%(k,v)
        elif isinstance(v,list):
            expression_attribute_values += "%s =list_append(if_not_exists(%s, []), %s),"%(k,k,v)
        else:
            expression_attribute_values += "%s= '%s',"%(k,v)


    try:
        # update the account in the database
        result = table.update_item(
            Key={
                'id': event['pathParameters']['id']
            },
            UpdateExpression='SET status= "Update work description",delegateAccountId= "12345",delegatePermission= "yes",submittedDate= "2020-05-20"',
            #expression_attribute_values[:-1],
            ReturnValues='ALL_NEW',
        )

        replace_decimals(result)

        # create a response
        response = {
            "statusCode": 200,
            "body": json.dumps(result['Attributes'])
        }
    except ClientError as ex:
        response = {
            "statusCode": 400,
            "body": json.dumps(expression_attribute_values[:-1])
           # "body": json.dumps(ex.response['Error']['Message'])
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