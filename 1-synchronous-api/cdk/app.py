#!/usr/bin/env python3
from constructs import Construct
from aws_cdk import App, Stack
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_dynamodb as _ddb
from aws_cdk import aws_apigateway as _ag
import aws_cdk as core

class CdkStack(core.Stack):
    def __init__(self, scope: Construct, id: str, stack_prefix: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here
        # Permissions

        lambda_role = _iam.Role(
            self,
            id='{}-lambda-role'.format(stack_prefix),
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'))

        cw_policy_statement = _iam.PolicyStatement(effect=_iam.Effect.ALLOW)
        cw_policy_statement.add_actions("logs:CreateLogGroup")
        cw_policy_statement.add_actions("logs:CreateLogStream")
        cw_policy_statement.add_actions("logs:PutLogEvents")
        cw_policy_statement.add_actions("logs:DescribeLogStreams")
        cw_policy_statement.add_resources("*")
        lambda_role.add_to_policy(cw_policy_statement)
        
        # Create Lambda Functions
        fn_lambda_invoice_service = _lambda.Function(
            self,
            '{}-lambda-invoice-service'.format(stack_prefix),
            code=_lambda.AssetCode("../sa-lambda/invoice-service/"),
            handler="app.lambda_handler",
            function_name='{}-lambda-invoice-service'.format(stack_prefix),
            role=lambda_role,            
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            runtime=_lambda.Runtime.PYTHON_3_8)

        

        fn_lambda_fullfilment_service = _lambda.Function(
            self,
            '{}-lambda-fulfillment-service'.format(stack_prefix),
            function_name='{}-lambda-fulfillment-service'.format(stack_prefix),
            code=_lambda.AssetCode("../sa-lambda/fullfilment-service/"),
            handler="app.lambda_handler",
            role=lambda_role,            
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            runtime=_lambda.Runtime.PYTHON_3_8)

        fn_lambda_forecasting_service = _lambda.Function(
            self,
            '{}-lambda-forecasting-service'.format(stack_prefix),
            function_name='{}-lambda-forecasting-service'.format(stack_prefix),
            code=_lambda.AssetCode("../sa-lambda/forecasting-service/"),
            handler="app.lambda_handler",
            role=lambda_role,            
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            runtime=_lambda.Runtime.PYTHON_3_8)

        lambda_policy_statement = _iam.PolicyStatement(effect=_iam.Effect.ALLOW)
        lambda_policy_statement.add_actions("lambda:InvokeFunction")
        lambda_policy_statement.add_resources("*")
        lambda_role.add_to_policy(lambda_policy_statement)
        
        fn_lambda_order_service = _lambda.Function(
            self,            
            '{}-lambda-order-service'.format(stack_prefix),
            function_name='{}-lambda-order-service'.format(stack_prefix),
            code=_lambda.AssetCode("../sa-lambda/order-service/"),
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(30),
            tracing=_lambda.Tracing.ACTIVE,
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)

        fn_lambda_order_service.add_environment(
            "FN_FORECASTING_SERVICE",
            fn_lambda_forecasting_service.function_arn)
        fn_lambda_order_service.add_environment(
            "FN_INVOICE_SERVICE", fn_lambda_invoice_service.function_arn)
        fn_lambda_order_service.add_environment(
            "FN_FULFILLMENT_SERVICE",
            fn_lambda_fullfilment_service.function_arn)

        api = _ag.RestApi(
            self,
            id='{}-api'.format(stack_prefix),)
        api_lambda_integration = _ag.LambdaIntegration(fn_lambda_order_service)

        api.root.add_resource('api').add_method('GET',
                                                  api_lambda_integration)


stack_prefix = 'eda-synchronousApiDemo'
app = core.App()
stack = CdkStack(app, stack_prefix, stack_prefix=stack_prefix)
core.Tags.of(stack).add('Name', stack_prefix)

app.synth()
