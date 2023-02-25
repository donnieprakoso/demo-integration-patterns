import boto3
import json
import os
import logging
import traceback
import time


logger = logging.getLogger()
logger.setLevel(logging.INFO)

WS_ENDPOINT = os.getenv('WS_ENDPOINT')


def response_proxy(data):
    '''
    For HTTP status codes, you can take a look at https://httpstatuses.com/
    '''
    try:
        response = {}
        response["isBase64Encoded"] = False
        response["statusCode"] = data["statusCode"]
        response["headers"] = {}
        if "headers" in data:
            response["headers"] = data["headers"]
        response["body"] = json.dumps(data["body"])
        return response
    except Exception:
        logger.info(traceback.format_exc())
        return {}


def prep_response(status_code, message):
    '''
    Function template for quick return response
    '''
    data = {}
    data["statusCode"] = status_code
    data["headers"] = {}
    data["body"] = {}
    data["body"]["message"] = message
    return response_proxy(data)


def load_connection():
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.getenv("TABLE_NAME"))
        response = table.scan()
        return response['Items']
    except Exception as e:
        logger.info(e)
        logger.error(e)
        return False

def delete_connection(connection_id):
    try:
        if connection_id:
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(os.getenv("TABLE_NAME"))
            table.delete_item(
                Key={
                    'connectionID': connection_id,
                }
            )
            return True
    except Exception as e:
        logger.info(e)
        logger.error(e)
        return False

def send_to_ws(connection_id, message):
    '''
    Function to send message using websocket connection
    '''
    try:
        ws_gateway = boto3.client('apigatewaymanagementapi', endpoint_url=WS_ENDPOINT)
        logger.info("Sending to {0} with message {1}".format(connection_id, message))
        ws_gateway.post_to_connection(
            Data=json.dumps(message),
            ConnectionId=connection_id
        )
        return True
    except Exception:
        logger.info(traceback.format_exc())
        delete_connection(connection_id)
        prep_response(500, "error")

def handler(event, context):
    '''
    Main function
    '''
    try:
        connection_id = event["requestContext"]["connectionId"]
        logger.info(event)
        logger.info(context)
        request_data = json.loads(event["body"])
        if 'token' in request_data:
            if request_data['token']=='e6bf488db98509c327a5a3af460be521':
                if (request_data['type']=='url' or request_data['type']=='title'):
                    data={}
                    data=(request_data['data'])
                    data['type']=request_data['type']
                    conns = load_connection()
                    for conn in conns:
                        send_to_ws(conn['connectionID'], data)
                return prep_response(200, "ok")
        else:
            if request_data['type']=='ping':
                send_to_ws(connection_id, 'pong')
            return prep_response(200, "ok") 
        return prep_response(401, "nok")
        # message = request_data["text"] if "text" in request_data else "Okay."
        # logger.info(message)
        # send_to_ws(connection_id, message)
        # time.sleep(5)
        # send_to_ws(connection_id, "Btw, AWS is working on the Asia Pacific (Jakarta) Region in Indonesia. Merdeka!")
    except Exception:
        logger.info(traceback.format_exc())
        prep_response(500, "error")

