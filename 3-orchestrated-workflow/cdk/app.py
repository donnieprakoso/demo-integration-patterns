#!/usr/bin/env python3
from constructs import Construct
from aws_cdk import App, Stack
from aws_cdk import aws_stepfunctions as _sfn
from aws_cdk import aws_stepfunctions_tasks as _tasks
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_ssm as _ssm
from aws_cdk import aws_lambda as _lambda
import aws_cdk as core
import json


class CdkStack(Stack):
    def __init__(self, scope: Construct, id: str, stack_prefix: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        lambda_role = _iam.Role(
            self,
            id="{}-iam-role".format(stack_prefix),
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'))

        cloudwatch_policy_statement = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW)
        cloudwatch_policy_statement.add_actions("logs:CreateLogGroup")
        cloudwatch_policy_statement.add_actions("logs:CreateLogStream")
        cloudwatch_policy_statement.add_actions("logs:PutLogEvents")
        cloudwatch_policy_statement.add_actions("logs:DescribeLogStreams")
        cloudwatch_policy_statement.add_resources("*")
        lambda_role.add_to_policy(cloudwatch_policy_statement)

        fn_lambda_inventory_process = _lambda.Function(
            self,
            "{}-lambda-inventory-process".format(stack_prefix),
            function_name="{}-lambda-inventory-process".format(stack_prefix),
            code=_lambda.AssetCode(
                "../lambda-functions/inventory-process/"),
            handler="app.handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_inventory_rollback = _lambda.Function(
            self,
            "{}-lambda-inventory-rollback".format(stack_prefix),
            function_name="{}-lambda-inventory-rollback".format(stack_prefix),
            code=_lambda.AssetCode(
                "../lambda-functions/inventory-rollback/"),
            handler="app.handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_payment_process = _lambda.Function(
            self,
            "{}-lambda-payment-process".format(stack_prefix),
            function_name="{}-lambda-payment-process".format(stack_prefix),
            code=_lambda.AssetCode(
                "../lambda-functions/payment-process/"),
            handler="app.handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_payment_rollback = _lambda.Function(
            self,
            "{}-lambda-payment-rollback".format(stack_prefix),
            function_name="{}-lambda-payment-rollback".format(stack_prefix),
            code=_lambda.AssetCode(
                "../lambda-functions/payment-rollback/"),
            handler="app.handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_logistic_process = _lambda.Function(
            self,
            "{}-lambda-logistic-process".format(stack_prefix),
            function_name="{}-lambda-logistic-process".format(stack_prefix),
            code=_lambda.AssetCode(
                "../lambda-functions/logistic-process/"),
            handler="app.handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fn_lambda_logistic_rollback = _lambda.Function(
            self,
            "{}-lambda-logistic-rollback".format(stack_prefix),
            function_name="{}-lambda-logistic-rollback".format(stack_prefix),
            code=_lambda.AssetCode(
                "../lambda-functions/logistic-rollback/"),
            handler="app.handler",
            tracing=_lambda.Tracing.ACTIVE,
            timeout=core.Duration.seconds(30),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)                                        

        task_inventory_process = _tasks.LambdaInvoke(
            self,
            "Inventory Process",
            lambda_function=fn_lambda_inventory_process,
            output_path="$.Payload"
        )

        task_inventory_rollback = _tasks.LambdaInvoke(
            self,
            "Inventory Rollback",
            lambda_function=fn_lambda_inventory_rollback,
            output_path="$.Payload"
        )

        task_payment_process = _tasks.LambdaInvoke(
            self,
            "Payment Process",
            lambda_function=fn_lambda_payment_process,
            output_path="$.Payload"
        )
        task_payment_rollback = _tasks.LambdaInvoke(
            self,
            "Payment Rollback",
            lambda_function=fn_lambda_payment_rollback,
            output_path="$.Payload"
        )

        task_logistic_process = _tasks.LambdaInvoke(
            self,
            "Logistic Process",
            lambda_function=fn_lambda_logistic_process,
            output_path="$.Payload"
        )
        task_logistic_rollback = _tasks.LambdaInvoke(
            self,
            "Logistic Rollback",
            lambda_function=fn_lambda_logistic_rollback,
            output_path="$.Payload"
        )


        state_succeed = _sfn.Succeed(self, "Transaction success")
        state_failed = _sfn.Fail(self, "Transaction failed")

        c_inventory_check = _sfn.Choice(self, "Inventory check ok?")
        c_inventory_check.when(_sfn.Condition.boolean_equals(
            "$.inventory_result", True), task_payment_process)
        c_inventory_check.when(_sfn.Condition.boolean_equals(
            "$.inventory_result", False), task_inventory_rollback)

        task_inventory_rollback.next(state_failed)

        c_payment_check = _sfn.Choice(self, "Payment check ok?")
        c_payment_check.when(_sfn.Condition.boolean_equals(
            "$.payment_result", True), task_logistic_process)
        c_payment_check.when(_sfn.Condition.boolean_equals(
            "$.payment_result", False), task_payment_rollback)

        task_payment_process.next(c_payment_check)
        task_payment_rollback.next(task_inventory_rollback)

        c_logistic_check = _sfn.Choice(self, "Logistic check ok?")
        c_logistic_check.when(_sfn.Condition.boolean_equals(
            "$.logistic_result", True), state_succeed)
        c_logistic_check.when(_sfn.Condition.boolean_equals(
            "$.logistic_result", False), task_logistic_rollback)

        task_logistic_process.next(c_logistic_check)
        task_logistic_rollback.next(task_payment_rollback)

        definition = task_inventory_process.next(c_inventory_check)
        _sfn.StateMachine(
            self,
            "{}-state-machine".format(stack_prefix),
            state_machine_name="{}-state-machine".format(stack_prefix),
            definition=definition,
            timeout=core.Duration.minutes(5))


stack_prefix = 'eda-saga-pattern'
app = core.App()
stack = CdkStack(app, stack_prefix, stack_prefix=stack_prefix)
core.Tags.of(stack).add('Name', stack_prefix)

app.synth()