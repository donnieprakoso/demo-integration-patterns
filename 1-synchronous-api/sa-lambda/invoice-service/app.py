import time

'''
Lambda func for invoice service
'''

def lambda_handler(event, context):
    print('invoice_service is called')
    time.sleep(1)
    response = {'status':200}
    return response
