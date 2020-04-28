import json
import logging
import os
import time
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    data = json.loads(event['body'])
    '''if 'profileId' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't create the account.")'''


    workmgnt_table = dynamodb.Table(os.environ['WORKMGNT_TABLE'])

    item = {
        'id': str(uuid.uuid1()),
        'accountId': data['accountId'],
        'orgId': data['orgId'],
        'type': data['type'],
        'deliveryType':data['deliveryType'],
        'category': data['category'],
        'industry': data['industry'],
        'selectionModel': data['selectionModel'],
        'startDate': data['startDate'],
        'endDate': data['endDate'],
        'estimatedEffort':data['estimatedEffort'],
        'description':data['description'],
        'outcome':data['outcome'],
        'rewardType':data['rewardType'],
        'rewardUnits':data['rewardUnits'],
        'rewardModel':data['rewardModel'],
        'criticalIndicator':data['criticalIndicator'],
        'internAllowedIndicator':data['internAllowedIndicator'],
        'travelIndicator':data['travelIndicator'],
        'skill': data['skill'],
        'attachments':data['attachments'],
    }

    # write the account to the database
    workmgnt_table.put_item(Item=item)

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(item)
    }

    return response


''' update item

 'status': data['status'],
 'delegateAccountId':data['delegateAccountId'],
 'delegatePermission':data['delegatePermission'],
 'submittedDate':data['submittedDate'],
        'reviewCompletedDate':data['reviewCompletedDate'],
        'reviewAccountId':data['reviewAccountId'],
        'reSubmittedDate':data['reSubmittedDate'],
        'closedDate':data['closedDate'],
        'closedAccountId':data['closedAccountId'], 
'''