import boto3
import os
import json
'''
Lambda func for order service
'''


def lambda_handler(event, context):
    print('order_service is called')
    response = {}
    try:
        client = boto3.client('lambda')
        resp_invoice=client.invoke(FunctionName=os.getenv("FN_INVOICE_SERVICE"),
                      InvocationType='RequestResponse')
        resp_fulfillment=client.invoke(FunctionName=os.getenv("FN_FULFILLMENT_SERVICE"),
                      InvocationType='RequestResponse')
        resp_forecasting=client.invoke(FunctionName=os.getenv("FN_FORECASTING_SERVICE"),
                      InvocationType='RequestResponse')
        data = {}
        data['invoice_service']=resp_invoice['ResponseMetadata']['HTTPStatusCode']
        data['fulfillment_service']=resp_fulfillment['ResponseMetadata']['HTTPStatusCode']
        data['forecasting_service']=resp_forecasting['ResponseMetadata']['HTTPStatusCode']
        print(data)
        response = {'statusCode': 200, 'body':json.dumps(data)}
    except Exception as e:
        print(e)
        response = {'statusCode': 500}
    return response
