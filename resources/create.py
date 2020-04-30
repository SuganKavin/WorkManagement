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

    workmgnt_table = dynamodb.Table(os.environ['WORKMGNT_TABLE'])
    workstatus_table = dynamodb.Table(os.environ['WORKMGNTSTATUS_TABLE'])

    work_detail = {}
    workid =str(uuid.uuid1())

    for k, v in data.items():
        work_detail[k] = v


    work_detail['id'] =workid

    # write the account to the database
    workmgnt_table.put_item(Item=work_detail)

    work_status = {}
    work_status_date =datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    work_status['id'] =workid
    work_status['status'] =data['status']
    work_status['statusDate'] =work_status_date
    work_status['statusTransition'] = [{ "status" : data['status'], "statusDate" :work_status_date}]

    workstatus_table.put_item(Item=work_status)
    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(work_detail)
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