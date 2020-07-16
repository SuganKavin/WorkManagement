from botocore.exceptions import ClientError
import os
import json
import boto3
import decimal
from boto3.dynamodb.conditions import Key
dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    table = dynamodb.Table(os.environ['WORKMGNT_TABLE'])
    if event['queryStringParameters'] is not None:
        accountId = event['queryStringParameters'].get('accountId')
        #status = event['queryStringParameters'].get('status')
        if accountId is None:  # or status is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"errCode": "LW_AC_001", "errMessage": "accountId is mandatory"})
            }
        else:
            try:
                poster_result = table.query(
                    IndexName='workmgnt_acctid-index',
                    KeyConditionExpression=Key('accountId').eq(
                        accountId),
                    # & Key('currentStatus').eq(status),
                    ScanIndexForward=False
                )
                print(poster_result)
                delegate_result = table.query(
                    IndexName='workmgnt_delegateid-index',
                    KeyConditionExpression=Key('delegateAccountId').eq(
                        accountId),
                    # & Key('currentStatus').eq(status),
                    ScanIndexForward=False
                )
                print(delegate_result)

                works = []
                orgId = ''
                if 'Items' in poster_result:
                    for work in poster_result['Items']:
                        workDetail = {}
                        orgId = work['orgId']
                        workDetail['workId'] = work['workId']
                        workDetail['currentStatus'] = work['currentStatus']
                        workDetail['delegateWork'] = False
                        workDetail['biddingEndDateTime'] = work['biddingEndDateTime']
                        workDetail['functionalDomain'] = work['functionalDomain']
                        skills = work['skills']
                        skillList = []
                        for skill in skills:
                            skillList.append(skill['skillName'])
                        workDetail['skills'] = skillList
                        workDetail['criticalWork'] = work['criticalWork']
                        works.append(workDetail)

                if 'Items' in delegate_result:
                    for work in delegate_result['Items']:
                        workDetail = {}
                        orgId = work['orgId']
                        workDetail['workId'] = work['workId']
                        workDetail['currentStatus'] = work['currentStatus']
                        workDetail['delegateWork'] = True
                        workDetail['biddingEndDateTime'] = work['biddingEndDateTime']
                        workDetail['functionalDomain'] = work['functionalDomain']
                        skills = work['skills']
                        skillList = []
                        for skill in skills:
                            skillList.append(skill['skillName'])
                        workDetail['skills'] = skillList
                        workDetail['criticalWork'] = work['criticalWork']
                        works.append(workDetail)

                worksDetail = {}
                worksDetail['accountId'] = accountId
                worksDetail['orgId'] = orgId
                worksDetail['Works'] = works

                replace_decimals(delegate_result)
                # create a response
                return {
                    "statusCode": 200,
                    "body": json.dumps(worksDetail)
                }
            except ClientError as ex:
                response = {
                    "statusCode": 400,
                    # "body": json.dumps(expression_attribute_values[:-1])
                    "body": json.dumps(ex.response['Error']['Message'])
                }
    elif event['pathParameters'] is not None:
        workId = event['pathParameters']['id']
        try:
            result = table.get_item(
                Key={
                    'workId': event['pathParameters']['id']
                }
            )
            replace_decimals(result)

            if 'Item' in result:
                # create a response
                return {
                    "statusCode": 200,
                    "body": json.dumps(result['Item'])
                }
            else:
                return {
                    "statusCode": 400,
                    "body": json.dumps("WorkId is not available")
                }
        except ClientError as ex:
            response = {
                "statusCode": 400,
                # "body": json.dumps(expression_attribute_values[:-1])
                "body": json.dumps(ex.response['Error']['Message'])
            }
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"errCode": "LW_AC_001", "errMessage": "accountId/status or workId is mandatory"})
        }


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
