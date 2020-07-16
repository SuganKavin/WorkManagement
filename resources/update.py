import json
import logging
import os
import boto3
import decimal
from botocore.exceptions import ClientError
from datetime import datetime

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    workmngt_data = json.loads(event['body'])

    id = event['pathParameters']['id']
    table = dynamodb.Table(os.environ['WORKMGNT_TABLE'])
    if not id:
        logging.error("Validation Failed. Missing id")
        raise Exception("Couldn't create the workid.")

    date = datetime.now()
    fromDateStr = date.strftime("%m/%d/%Y %H:%M:%S")
    expressionAttributeValues = {}
    updateExpression = 'SET '
    for k, v in workmngt_data.items():
        expressionAttributeValues[':%s' % (k)] = v
        if k == 'delegatePermission':
            updateExpression += '%s=:%s,' % (k, k)
        elif k == 'status':
            updateExpression += '%s=:%s,' % ('currentStatus', k)
        elif isinstance(v, list):
            updateExpression += "%s=list_append(%s,:%s)," % (k, k, k)
        else:
            updateExpression += '%s=:%s,' % (k, k)
    expressionAttributeValues[':currentStatusDate'] = fromDateStr
    updateExpression += '%s=:%s,' % ('CurrentStatusDate', 'currentStatusDate')

    status_transition = []
    status = {}
    status['status'] = workmngt_data['status']
    status['date'] = fromDateStr
    if 'changedBy' in workmngt_data:
        status['changedBy'] = workmngt_data['changedBy']
    else:
        status['changedBy'] = workmngt_data['accountId']
    status_transition.append(status)

    expressionAttributeValues[':statustransition'] = status_transition
    updateExpression += "%s=list_append(%s,:%s)" % (
        'statusTransition', 'statusTransition', 'statustransition')

    print(expressionAttributeValues)
    print(updateExpression)

    try:
        # update the account in the database
        result = table.update_item(
            Key={
                'workId': event['pathParameters']['id']
            },
            ExpressionAttributeValues=expressionAttributeValues,
            UpdateExpression=updateExpression,
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
