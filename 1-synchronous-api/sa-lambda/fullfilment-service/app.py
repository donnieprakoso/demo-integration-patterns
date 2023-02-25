import time

'''
Lambda func for fullfilment service
'''

def lambda_handler(event, context):
    print('fullfilment_service is called')
    time.sleep(1)
    response = {'status':200}
    return response
