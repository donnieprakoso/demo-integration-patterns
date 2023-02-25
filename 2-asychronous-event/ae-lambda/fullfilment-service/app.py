import time
import boto3
import json
import os

EVENT_BUS_NAME=os.getenv("EVENT_BUS_NAME")

'''
Lambda func for fulfillment service
'''

def lambda_handler(event, context):
    print(event)
    print('invoice_service is called')
    time.sleep(10)
    
    payload = {}
    payload['token']='e6bf488db98509c327a5a3af460be521'
    payload['message']='fulfillment_completed'

    client = boto3.client('events')
    response = client.put_events(Entries=[
        {
            'Source': 'order_service',
            'DetailType': 'notification',
            'Detail': json.dumps(payload),
            'EventBusName': EVENT_BUS_NAME
        },
    ])
    response = client.put_events(Entries=[
        {
            'Source': 'fulfillment_service',
            'DetailType': 'fulfilment_completed',
            'Detail': json.dumps(payload),
            'EventBusName': EVENT_BUS_NAME
        },
    ])
    response = {'status':200}
    return response
