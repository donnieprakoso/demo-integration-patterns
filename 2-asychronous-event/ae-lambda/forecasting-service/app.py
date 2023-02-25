import time

'''
Lambda func for forecasting service
'''

def lambda_handler(event, context):
    print(event)
    print('forecasting_service is called')
    time.sleep(1)
    response = {'status':200}
    return response
