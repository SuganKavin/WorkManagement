import os
import json
import boto3
import decimal

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    table = dynamodb.Table(os.environ['WORKMGNT_TABLE'])

    result = table.get_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )

    if 'Item' in result:
        replace_decimals(result)
        # create a response
        response = {
            "statusCode": 200,
            "body": json.dumps(result['Item'])
        }
    else:
        response = {
            "statusCode": 400,
            "body": json.dumps("WorkId is not available")
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