import os
import boto3

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    table = dynamodb.Table(os.environ['WORKMGNT_TABLE'])

    table.delete_item(
        Key={
            'workId': event['pathParameters']['id']
        }
    )

    # create a response
    response = {
        "statusCode": 200
    }

    return response