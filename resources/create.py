from decimal import Decimal
import json
import logging
import os
import time
import uuid
import boto3
from datetime import datetime
from dateutil.relativedelta import *
from botocore.exceptions import ClientError
from boto3 import client as boto3_client

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3_client('lambda')


def handler(event, context):
    data = json.loads(event['body'])

    if 'accountId' not in data or 'orgId' not in data:
        logging.error("Validation Failed. accountId/orgId is missing")
        response = {"body": json.dumps(
            {"errMessage": "accountId/orgId is missing"}), "statusCode": 400}
        return response

    workmgnt_table = dynamodb.Table(os.environ['WORKMGNT_TABLE'])

    date = datetime.utcnow()
    fromDateStr = date.strftime("%m/%d/%Y %H:%M:%S")
    workIdDateStr = date.strftime("%m%d%Y_%H%M%S")
    status = {}
    if 'status' not in data:
        status['status'] = 'Posted'
    else:
        status['status'] = data['status']
    status['date'] = fromDateStr
    if 'changedBy' in data:
        status['changedBy'] = data['changedBy']
    else:
        status['changedBy'] = data['accountId']
    statusTransition = [status]

    workmgnt_detail = {}
    if 'biddingEndDateTime' not in data:
        workStartDateStr = data['plannedStartDate']
        biddingEndDate = datetime.strptime(
            workStartDateStr, "%m-%d-%Y") + relativedelta(days=-1)
        workmgnt_detail['biddingEndDateTime'] = biddingEndDate.strftime(
            "%m/%d/%Y")

    workmgnt_detail['currentStatus'] = 'Posted'
    workmgnt_detail['CurrentStatusDate'] = fromDateStr
    workmgnt_detail['postedDate'] = fromDateStr
    workmgnt_detail['UpdatedAt'] = fromDateStr
    workmgnt_detail['statusTransition'] = statusTransition
    workmgnt_detail['workId'] = data['accountId'] + \
        "_" + data['orgId']+"_"+workIdDateStr

    for k, v in data.items():
        workmgnt_detail[k] = v

    print(workmgnt_detail)
    # write the account to the database
    try:
        wallet_item = {
            'id': data['accountId']+'WB'
        }
        wallet_response = lambda_client.invoke(FunctionName="get-wallet-balance",
                                               InvocationType='RequestResponse',
                                               Payload=json.dumps(wallet_item))

        print(wallet_response)

        payload = wallet_response['Payload']
        t = payload.read()
        print(t)
        #res = json.loads(t['body'])
        # print(res)
        # print(payload.read())
        # [ERROR] JSONDecodeError: Expecting value: line 1 column 1 (char 0) Traceback (most recent call last):
        # print(json.load(wallet_response['Payload']))
        #walletbody = json.loads(json.loads(payload.read())['body'])

        # print(walletbody['curBal'])
        currentBalance = 1000

        if currentBalance < workmgnt_detail['rewardUnits']:
            logging.error(
                "Validation Failed. wallet balance is less than the work allocated amount")
            response = {"body": json.dumps(
                {"errMessage": "wallet balance is less than the work allocated amount"}), "statusCode": 400}
            return response

        workmgnt_table.put_item(Item=workmgnt_detail)
        # create a response
        response = {
            "statusCode": 200,
            "body": json.dumps(workmgnt_detail)
        }

        transaction_item = {
            'orgId': data['orgId'],
            'sendWalId':  data['accountId']+'WB',
            'type': 'Reserve',
            'reason': workmgnt_detail['workId'],
            'amt': workmgnt_detail['rewardUnits'],
            'currency': 'points',
            'sendBal': currentBalance
        }

        lambda_client.invoke(FunctionName="transfer",
                             InvocationType='Event',
                             Payload=json.dumps(transaction_item))

    except ClientError as ex:
        response = {
            "statusCode": 400,
            # "body": json.dumps(expression_attribute_values[:-1])
            "body": json.dumps(ex.response['Error']['Message'])
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


class DecimalDecoder(json.JSONDecoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalDecoder, self).default(o)
