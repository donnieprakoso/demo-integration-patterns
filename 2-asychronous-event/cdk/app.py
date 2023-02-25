#!/usr/bin/env python3
from constructs import Construct
from aws_cdk import App, Stack
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_dynamodb as _ddb
from aws_cdk import aws_apigateway as _ag
from aws_cdk import aws_events as _eb
from aws_cdk import aws_events_targets as _ebt
from aws_cdk import aws_apigatewayv2_alpha as _apigwv2
from aws_cdk import aws_s3_assets as _s3assets
from aws_cdk.aws_apigatewayv2_integrations_alpha import WebSocketLambdaIntegration
from aws_cdk import aws_amplify_alpha as _amplify
import os
import aws_cdk as core

class CdkStack(core.Stack):
    def __init__(self, scope: Construct, id: str, stack_prefix: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ddb_table = _ddb.Table(
            self,
            id='{}-websocket'.format(stack_prefix),
            table_name='{}-websocket'.format(stack_prefix),
            partition_key=_ddb.Attribute(name='connectionID',
                                         type=_ddb.AttributeType.STRING),
            removal_policy=core.RemovalPolicy.
            DESTROY,  # THIS IS NOT RECOMMENDED FOR PRODUCTION USE
            read_capacity=10,
            write_capacity=10)

        eb = _eb.EventBus(
            self, id="{}-eventbus".format(stack_prefix), event_bus_name="{}-eventbus".format(stack_prefix))

        lambda_role = _iam.Role(
            self,
            id="{}-role-service".format(stack_prefix),
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'))

        notification_role = _iam.Role(
            self,
            id="{}-role-notification".format(stack_prefix),
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'))


        dynamodb_policy_statement = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW)
        dynamodb_policy_statement.add_actions("dynamodb:*")
        dynamodb_policy_statement.add_resources(ddb_table.table_arn)
        notification_role.add_to_policy(dynamodb_policy_statement)

        eventbridge_policy_statement = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW)
        eventbridge_policy_statement.add_actions("events:*")
        eventbridge_policy_statement.add_resources(eb.event_bus_arn)
        lambda_role.add_to_policy(eventbridge_policy_statement)

        cloudwatch_policy_statement = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW)
        cloudwatch_policy_statement.add_actions("logs:CreateLogGroup")
        cloudwatch_policy_statement.add_actions("logs:CreateLogStream")
        cloudwatch_policy_statement.add_actions("logs:PutLogEvents")
        cloudwatch_policy_statement.add_actions("logs:DescribeLogStreams")
        cloudwatch_policy_statement.add_resources("*")
        lambda_role.add_to_policy(cloudwatch_policy_statement)
        notification_role.add_to_policy(cloudwatch_policy_statement)

        

        fn_lambda_invoice_service = _lambda.Function(
            self,
            "{}-lambda-invoice".format(stack_prefix),
            function_name="{}-lambda-invoice".format(stack_prefix),
            code=_lambda.AssetCode("../ae-lambda/invoice-service/"),
            handler="app.lambda_handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_invoice_service.add_environment("EVENT_BUS_NAME",eb.event_bus_name)

        fn_lambda_fulfilment_service = _lambda.Function(
            self,
            "{}-lambda-fulfilment".format(stack_prefix),
            function_name="{}-lambda-fulfilment".format(stack_prefix),
            code=_lambda.AssetCode("../ae-lambda/fullfilment-service/"),
            handler="app.lambda_handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_fulfilment_service.add_environment("EVENT_BUS_NAME",eb.event_bus_name)

        fn_lambda_forecasting_service = _lambda.Function(
            self,
            "{}-lambda-forecasting".format(stack_prefix),
            function_name="{}-lambda-forecasting".format(stack_prefix),
            code=_lambda.AssetCode("../ae-lambda/forecasting-service/"),
            handler="app.lambda_handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_forecasting_service.add_environment("EVENT_BUS_NAME",eb.event_bus_name)

        fn_lambda_order_service = _lambda.Function(
            self,
            "{}-lambda-order".format(stack_prefix),
            function_name="{}-lambda-order".format(stack_prefix),
            code=_lambda.AssetCode("../ae-lambda/order-service/"),
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(30),
            tracing=_lambda.Tracing.ACTIVE,
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_order_service.add_environment("EVENT_BUS_NAME",eb.event_bus_name)

        fn_lambda_logistic_service = _lambda.Function(
            self,
            "{}-lambda-logistic".format(stack_prefix),
            function_name="{}-lambda-logistic".format(stack_prefix),
            code=_lambda.AssetCode("../ae-lambda/logistic-service/"),
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(30),
            tracing=_lambda.Tracing.ACTIVE,
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_logistic_service.add_environment("EVENT_BUS_NAME",eb.event_bus_name)

        fn_lambda_notification_service = _lambda.Function(
            self,
            "{}-lambda-notification".format(stack_prefix),
            function_name="{}-lambda-notification".format(stack_prefix),
            code=_lambda.AssetCode("../ae-lambda/notification-service/"),
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(30),
            tracing=_lambda.Tracing.ACTIVE,
            role=notification_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        

        eb_order_created_pattern = _eb.EventPattern(
            detail_type=["order_created"], )
        eb_fulfilment_completed_pattern = _eb.EventPattern(
            detail_type=["fulfilment_completed"], )
        eb_notification_pattern = _eb.EventPattern(
            detail_type=["notification"], )        
        
        eb_order_created_rule = _eb.Rule(
            self,
            id="{}-rule-orderCreated".format(stack_prefix),
            description="Order created event",
            enabled=True,
            event_bus=eb,
            event_pattern=eb_order_created_pattern,
            rule_name="{}-rule-ordercreated".format(stack_prefix),
            targets=[
                _ebt.LambdaFunction(handler=fn_lambda_invoice_service),
                _ebt.LambdaFunction(handler=fn_lambda_fulfilment_service),
                _ebt.LambdaFunction(handler=fn_lambda_forecasting_service)
            ])

        eb_fulfilment_completed_rule = _eb.Rule(
            self,
            id="{}-rule-fulfilmentCompleted".format(stack_prefix),
            description="Fulfilment completed event",
            enabled=True,
            event_bus=eb,
            event_pattern=eb_fulfilment_completed_pattern,
            rule_name="{}-rule-fulfilmentCompleted".format(stack_prefix),
            targets=[_ebt.LambdaFunction(handler=fn_lambda_logistic_service)])
    
        eb_notification_rule = _eb.Rule(
            self,
            id="{}-rule-notification".format(stack_prefix),
            description="Notification event",
            enabled=True,
            event_bus=eb,
            event_pattern=eb_notification_pattern,
            rule_name="{}-rule-notification".format(stack_prefix),
            targets=[_ebt.LambdaFunction(handler=fn_lambda_notification_service)])


        api = _ag.RestApi(
            self,
            id="{}-restapi".format(stack_prefix),
            
        )
        api_lambda_integration = _ag.LambdaIntegration(fn_lambda_order_service)
        api.root.add_resource('test').add_method('GET',
                                                 api_lambda_integration)

        # Websocket
        fn_lambda_on_connect = _lambda.Function(
            self,
            "{}-lambda-onConnect".format(stack_prefix),
            function_name="{}-lambda-onConnect".format(stack_prefix),
            code=_lambda.AssetCode("../ws-lambda/on-connect/"),
            handler="app.handler",
            timeout=core.Duration.seconds(30),
            tracing=_lambda.Tracing.ACTIVE,
            role=notification_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_on_connect.add_environment("TABLE_NAME",ddb_table.table_name)

        fn_lambda_on_disconnect = _lambda.Function(
            self,
            "{}-lambda-onDisconnect".format(stack_prefix),
            function_name="{}-lambda-onDisconnect".format(stack_prefix),
            code=_lambda.AssetCode("../ws-lambda/on-disconnect/"),
            handler="app.handler",
            timeout=core.Duration.seconds(30),
            tracing=_lambda.Tracing.ACTIVE,
            role=notification_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_on_disconnect.add_environment("TABLE_NAME",ddb_table.table_name)

        fn_lambda_on_message = _lambda.Function(
            self,
            "{}-lambda-onMessage".format(stack_prefix),
            function_name="{}-lambda-onMessage".format(stack_prefix),
            code=_lambda.AssetCode("../ws-lambda/on-message/"),
            handler="app.handler",
            timeout=core.Duration.seconds(30),
            tracing=_lambda.Tracing.ACTIVE,
            role=notification_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_on_message.add_environment("TABLE_NAME",ddb_table.table_name)

        ws_api = _apigwv2.WebSocketApi(self, 
                                       "{}-ws-api".format(stack_prefix),
                                       route_selection_expression="$request.body.message",
                                       connect_route_options=_apigwv2.WebSocketRouteOptions(integration=WebSocketLambdaIntegration("ConnectIntegration",fn_lambda_on_connect)),
                                       disconnect_route_options=_apigwv2.WebSocketRouteOptions(integration=WebSocketLambdaIntegration("DisconnectIntegration",fn_lambda_on_disconnect)),
                                       )
        ws_api_dev = _apigwv2.WebSocketStage(self, "dev",
            web_socket_api=ws_api,
            stage_name="dev",
            auto_deploy=True
        )
        ws_api.add_route("sendmessage",
            integration=WebSocketLambdaIntegration("SendMessageIntegration", fn_lambda_on_message)
        )        

        ws_api.grant_manage_connections(fn_lambda_notification_service)

        fn_lambda_notification_service.add_environment(
            "WS_ENDPOINT",
            ws_api_dev.callback_url)
        fn_lambda_notification_service.add_environment(
            "TABLE_NAME", ddb_table.table_name)


        core.CfnOutput(self,
                       "{}-output-dynamodbTable".format(stack_prefix),
                       value=ddb_table.table_name,
                       export_name="{}-ddbTable".format(stack_prefix))
        core.CfnOutput(self,
                       "{}-output-apiEndpointURL".format(stack_prefix),
                       value=api.url,
                       export_name="{}-apiEndpointURL".format(stack_prefix))
        core.CfnOutput(self,
                       "{}-output-wsApiEndpointURL".format(stack_prefix),
                       value=ws_api_dev.url,
                       export_name="{}-wsApiEndpointURL".format(stack_prefix))
        core.CfnOutput(self,
                       "{}-output-wsApiCallbackURL".format(stack_prefix),
                       value=ws_api_dev.callback_url,
                       export_name="{}-wsApiCallbackURL".format(stack_prefix))                



stack_prefix = 'eda-asynchronousApiDemo'
app = core.App()
stack = CdkStack(app, stack_prefix, stack_prefix=stack_prefix)
core.Tags.of(stack).add('Name', stack_prefix)

app.synth()
