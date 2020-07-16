import json
import logging
import os
import boto3

from botocore.exceptions import ClientError
from datetime import datetime

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    #data = json.loads(event['body'])
    data = event
    print(data)
    if 'orgId' not in data or 'sendWalId' not in data or 'type' not in data or 'amt' not in data or 'reason' not in data or 'currency' not in data or 'sendBal' not in data:
        logging.error("Validation Failed. orgId/sendWalId/type/amt/reason/currency/sendBal is mandatory to proceed transfer")
        response = {"body": json.dumps({"errMessage": "orgId/sendWalId/type/amt/reason/currency/sendBal is mandatory to proceed transfer"}), "statusCode": 400}
        return response
    
    type_set = {"Reserve", "Reverse", "Credit", "Debit", "Redeem"}
    if data['type'] not in type_set:
        response = {"body": json.dumps({"errMessage": "Invalid type value"}), "statusCode": 400}
        return response

    type_reserve = "Reserve"
    type_reverse = "Reverse"
    type_credit = "Credit"
    type_redeem = "Redeem"
    type_debit = "Debit"


    trx_table = dynamodb.Table(os.environ['TRANSACTION_TABLE'])
    wallet_table = dynamodb.Table(os.environ['WALLET_TABLE'])

    currentTime = datetime.now()
    sender_transaction_detail = {}
    for k, v in data.items():
        if 'orgId' == k  or 'type' == k or 'amt'  == k or 'reason' == k or 'currency' == k or 'comments' == k:
            sender_transaction_detail[k] = v
    sender_transaction_detail['walId'] = data['sendWalId']
    sender_transaction_detail['date'] = currentTime.strftime("%d/%m/%Y %H:%M:%S")
    sender_transaction_detail['id'] = currentTime.replace(microsecond=0).isoformat()

    try:
        if data['type'] == type_reserve:
            print('reserve transaction')
            sender_transaction_detail['balance'] = data['sendBal'] - data['amt']
            print(sender_transaction_detail)
            print( data['sendWalId'])
            wallet_table.update_item(
                Key={
                    'id': data['sendWalId']
                },
                ExpressionAttributeValues={
                    ':updatedAt': currentTime.strftime("%d/%m/%Y %H:%M:%S"),
                    ':amt': data['amt'],
                },
                UpdateExpression='SET curBal = curBal - :amt, resvBal = resvBal + :amt, updatedAt = :updatedAt',
                ReturnValues='ALL_NEW',
            )
            print('reserve transaction wallet completed')
            trx_table.put_item(Item=sender_transaction_detail)
            print('reserve transaction completed')
        elif data['type'] == type_reverse:

            sender_transaction_detail['balance'] = data['sendBal'] + data['amt']

            wallet_table.update_item(
                Key={
                    'id': data['sendWalId']
                },
                ExpressionAttributeValues={
                    ':updatedAt': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    ':amt': data['amt'],
                },
                UpdateExpression='SET curBal = curBal + :amt, resvBal = resvBal - :amt, updatedAt = :updatedAt',
                ReturnValues='ALL_NEW',
            )

            trx_table.put_item(Item=sender_transaction_detail)
        elif data['type'] == type_redeem:

            sender_transaction_detail['balance'] = data['sendBal'] - data['amt']

            wallet_table.update_item(
                Key={
                    'id': data['sendWalId']
                },
                ExpressionAttributeValues={
                    ':updatedAt': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    ':amt': data['amt'],
                },
                UpdateExpression='SET curBal = curBal - :amt, updatedAt = :updatedAt',
                ReturnValues='ALL_NEW',
            )

            trx_table.put_item(Item=sender_transaction_detail)
        elif data['type'] == type_debit:
            if 'recvWalId' not in data  or  'allocatedAmt' not in data:
                logging.error("Validation Failed. recvWalId/allocatedAmt is missing")
                response = {"body": json.dumps({"errMessage": "recvWalId/allocatedAmt is missing"}), "statusCode": 400}
                return response

            if 'Budget' == data['reason']:
                if not (data['sendWalId'].endswith("WB") and data['recvWalId'].endswith("WB")):
                    response = {"body": json.dumps({"errMessage": "Transfer between business wallet for reason:Budget"}), "statusCode": 400}
                    return response
            if 'Personal' == data['reason']:
                if not (data['sendWalId'].endswith("WP") and data['recvWalId'].endswith("WP")):
                    response = {"body": json.dumps({"errMessage": "Transfer between personal wallet for reason:Personal"}), "statusCode": 400}
                    return response

            receiver_wallet_result = wallet_table.get_item(
                Key={
                    'id': data['recvWalId']
                }
            )
            status = data['type']
            balance = 0

            if data['allocatedAmt'] == data['amt']:
                status = 'Closure'
                balance = 0
            else:
                status = 'Partial Closure'
                balance = data['allocatedAmt'] - data['amt']

            if 'Item' not in receiver_wallet_result:
                response = {
                    "body": json.dumps({"errMessage": "Receiver wallet is not exists"}),
                    "statusCode": 400}
                return response

            sender_transaction_detail['id'] =  data['recvWalId']+ "#" +currentTime.replace(microsecond=0).isoformat()
            sender_transaction_detail['balance'] = data['sendBal'] + balance

            receiver_transaction_detail = {}

            receiver_transaction_detail['id'] = data['sendWalId'] +"#" +currentTime.replace(microsecond=0).isoformat()
            receiver_transaction_detail['orgId'] = data['orgId']
            receiver_transaction_detail['walId'] = data['recvWalId']
            receiver_transaction_detail['date'] = currentTime.strftime("%d/%m/%Y %H:%M:%S")
            receiver_transaction_detail['type'] = type_credit
            receiver_transaction_detail['reason'] = data['reason']
            receiver_transaction_detail['amt'] = data['amt']
            receiver_transaction_detail['currency'] = data['currency']
            receiver_transaction_detail['balance'] = receiver_wallet_result['Item']['curBal'] + data['amt']
            if 'comments' in data:
                receiver_transaction_detail['comments'] = data['comments']

            with trx_table.batch_writer() as batch:
                batch.put_item(
                    Item= sender_transaction_detail)
                batch.put_item(
                    Item= receiver_transaction_detail)

            wallet_table.update_item(
                Key={
                    'id': data['sendWalId']
                },
                ExpressionAttributeValues={
                    ':updatedAt': currentTime.strftime("%d/%m/%Y %H:%M:%S"),
                    ':balance' : balance,
                    ':amt' :data['allocatedAmt'],
                },
                UpdateExpression='SET curBal = curBal + :balance, resvBal = resvBal - :amt, updatedAt = :updatedAt',
                ReturnValues='ALL_NEW',
            )

            wallet_table.update_item(
                Key={
                    'id': data['recvWalId']
                },
                ExpressionAttributeValues={
                    ':updatedAt': currentTime.strftime("%d/%m/%Y %H:%M:%S"),
                    ':balance' : data['amt'],
                },
                UpdateExpression='SET curBal = curBal + :balance, updatedAt = :updatedAt',
                ReturnValues='ALL_NEW',
            )

        response = {
            "statusCode": 200
        }
        return response

    except ClientError as ex:
        response = {
            "statusCode": 400,
            "body": json.dumps(ex.response['Error']['Message'])
        }