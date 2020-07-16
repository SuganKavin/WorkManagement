import json
import logging
import os
import time
import uuid
import boto3
from datetime import datetime
import decimal
dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    data = event  # json.loads(event['body'])
    wallet_table = dynamodb.Table(os.environ['WALLET_TABLE'])

    wallet_response = wallet_table.get_item(
        Key={
            'id': data['id']
        }
    )

    '''wallet_response = table.get_item(
        Key={
            'id': data['id']
        },
        'ConsistentRead': True
    )'''
    if 'Item' in wallet_response:
        # replace_decimals(wallet_response)
        # DecimalEncoder(wallet_response)
        # create a response
        print(wallet_response['Item']['curBal'])
        print(type(wallet_response['Item']['curBal']))
        # Converting string into int
        #string_to_int = int(string)

        # Show the Data type
        # print(type(string_to_int))

        balance = {}
        balance['curBal'] = int(wallet_response['Item']['curBal'])

        response = {
            'statusCode': 200,
            'body': int(wallet_response['Item']['curBal'])
            # "body": json.dumps(wallet_response['Item'], indent=4, cls=DecimalEncoder)
        }
    else:
        response = {
            "statusCode": 400,
            "body": json.dumps("id is not available")
        }
    return response


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def replace_decimals(obj):
    if isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj
