import time
import boto3
import json
import os

'''
Lambda func for logistic service
'''

EVENT_BUS_NAME=os.getenv("EVENT_BUS_NAME")

def lambda_handler(event, context):
    print(event)
    print('invoice_service is called')
    time.sleep(0)
    
    payload = {}
    payload['token']='e6bf488db98509c327a5a3af460be521'
    payload['message']='logistic_started'

    client = boto3.client('events')
    response = client.put_events(Entries=[
        {
            'Source': 'logistic_service',
            'DetailType': 'notification',
            'Detail': json.dumps(payload),
            'EventBusName': EVENT_BUS_NAME
        },
    ])
    response = {'status':200}
    return response
