import json
import logging
import os
import time
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    #data = event
    data = json.loads(event['body'])

    if 'accountId' not in data or 'action' not in data:
        logging.error(
            "Validation Failed. accountId/action is not present in the request")
        response = {"body": json.dumps(
            {"errMessage": "accountId/action is not present in the request"}), "statusCode": 400}
        return response

    walId_BW = data['accountId'] + "WB"
    walId_PW = data['accountId'] + "WP"

    table = dynamodb.Table(os.environ['WALLET_TABLE'])

    wallet = table.get_item(
        Key={
            'id': walId_BW
        }
    )

    if data['action'] == 'Create' or data['action'] == 'Delete':

        if data['action'] == 'Create' and 'currency' not in data:
            logging.error(
                "Validation Failed. currency is not present in the request")
            response = {"body": json.dumps(
                {"errMessage": "currency is not present in the request"}), "statusCode": 400}
            return response

        elif data['action'] == 'Create':
            if 'Item' in wallet:
                response = {
                    "body": json.dumps({"errMessage": "wallet already exists"}),
                    "statusCode": 400}
                return response

            createdAt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            bwal_detail = {
                'currency': data['currency'],
                'accountId': data['accountId'],
                'curBal': 0,
                'resvBal': 0,
                'id': walId_BW,
                'createdAt': createdAt
            }

            pwal_detail = {
                'currency': data['currency'],
                'accountId': data['accountId'],
                'curBal': 0,
                'resvBal': 0,
                'id': walId_PW,
                'createdAt': createdAt
            }

            with table.batch_writer() as batch:
                batch.put_item(
                    Item=bwal_detail)
                batch.put_item(
                    Item=pwal_detail)

        elif data['action'] == 'Delete':
            if 'Item' not in wallet:
                response = {
                    "body": json.dumps({"errMessage": "wallet not exists"}),
                    "statusCode": 400}
                return response
            with table.batch_writer() as batch:
                batch.delete_item(
                    Key={
                        'id': walId_BW
                    })
                batch.delete_item(
                    Key={
                        'id': walId_PW
                    })

        response = {
            "statusCode": 200
        }
        return response
    else:
        logging.error(
            "Validation Failed. action values should be create/delete")
        response = {"body": json.dumps(
            {"errMessage": "action values should be create/delete"}), "statusCode": 400}
        return response
