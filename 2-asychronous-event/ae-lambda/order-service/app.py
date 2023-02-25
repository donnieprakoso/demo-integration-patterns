import boto3
import os
import json
'''
Lambda func for order service
'''

EVENT_BUS_NAME=os.getenv("EVENT_BUS_NAME")

def lambda_handler(event, context):
    print(event)
    try:
        data = {}
        data['metadata']={"service":"demo-eventbridge"}
        data['data']={}
        data['data']['id']='ABC12345'
        data['data']['customer']={'first_name':'Test','last_name':'Test'}
        data['data']['order']={'total':100,'currency':'SGD','billing_address':'Address 12345, Singapore'}
        data['data']['line_items']=[]
        ex_item={
            'sku':'12345',
            'item_name':'Item name testing',
            'quantity':1
        }
        data['data']['line_items'].append(ex_item)
        ex_item={
            'sku':'23456',
            'item_name':'Item name testing',
            'quantity':1
        }
        data['data']['line_items'].append(ex_item)
        client = boto3.client('events')
        response = client.put_events(Entries=[
            {
                'Source': 'order_service',
                'DetailType': 'order_created',
                'Detail': json.dumps(data),
                'EventBusName': EVENT_BUS_NAME
            },
        ])
        print(response)
        payload = {}
        payload['token']='e6bf488db98509c327a5a3af460be521'
        payload['message']='order_received'

        response = client.put_events(Entries=[
            {
                'Source': 'order_service',
                'DetailType': 'notification',
                'Detail': json.dumps(payload),
                'EventBusName': EVENT_BUS_NAME
            },
        ])
        print(response)
        response = {'statusCode': 200, 'body':json.dumps("{}")}
        return response
    except Exception as e:
        print(e)
        response = {'statusCode': 500, 'body':json.dumps("{}")}
        return response
