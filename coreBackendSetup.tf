provider "aws" {
  region = "me-south-1"
}

resource "aws_api_gateway_rest_api" "rers_api" {
    name        = "RERS_API"
    description = "API Gateway for Road Emergency Reporting System"
}

resource "aws_api_gateway_resource" "event_resource" {
    rest_api_id = aws_api_gateway_rest_api.rers_api.id
    parent_id   = aws_api_gateway_rest_api.rers_api.root_resource_id
    path_part   = "event"
}

resource "aws_api_gateway_method" "get_event_report" {
    rest_api_id   = aws_api_gateway_rest_api.rers_api.id
    resource_id   = aws_api_gateway_resource.event_resource.id
    http_method   = "GET"
    authorization = "NONE"
}

resource "aws_api_gateway_method" "post_event" {
    rest_api_id   = aws_api_gateway_rest_api.rers_api.id
    resource_id   = aws_api_gateway_resource.event_resource.id
    http_method   = "POST"
    authorization = "NONE"
    request_models = {
        "application/json" = "Empty"
    }
}

resource "aws_lambda_function" "record_event_lambda" {
    function_name = "record_event_lambda"
    handler       = "record_event_lambda.lambda_handler"
    runtime       = "python3.8"
    role          = aws_iam_role.lambda_exec.arn
    filename      = "record_event_lambda.zip"
    source_code_hash = filebase64sha256("record_event_lambda.zip")
}

resource "aws_iam_role" "lambda_exec" {
    name = "lambda_exec_role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Principal = {
                    Service = "lambda.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        ]
    })
}

resource "aws_iam_policy" "lambda_dynamodb_policy" {
    name        = "lambda_dynamodb_policy-5"
    description = "IAM policy for Lambda to access DynamoDB"
    policy      = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "dynamodb:PutItem"
                ]
                Resource = "*"
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_exec_policy_attachment" {
    role       = aws_iam_role.lambda_exec.name
    policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
    role       = aws_iam_role.lambda_exec.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_ec2_policy" {
    role       = aws_iam_role.lambda_exec.name
    policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_api_gateway_integration" "get_event_integration" {
    rest_api_id             = aws_api_gateway_rest_api.rers_api.id
    resource_id             = aws_api_gateway_resource.event_resource.id
    http_method             = aws_api_gateway_method.get_event_report.http_method
    type                    = "AWS_PROXY"
    integration_http_method = "POST"
    uri                     = aws_lambda_function.record_event_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "post_event_integration" {
    rest_api_id             = aws_api_gateway_rest_api.rers_api.id
    resource_id             = aws_api_gateway_resource.event_resource.id
    http_method             = aws_api_gateway_method.post_event.http_method
    type                    = "AWS_PROXY"
    integration_http_method = "POST"
    uri                     = aws_lambda_function.record_event_lambda.invoke_arn
}

resource "aws_api_gateway_deployment" "deployment" {
    rest_api_id = aws_api_gateway_rest_api.rers_api.id
    depends_on  = [aws_api_gateway_integration.get_event_integration, aws_api_gateway_integration.post_event_integration]
    description = "Deployment for RERS API"
}

resource "aws_api_gateway_stage" "prod" {
    deployment_id = aws_api_gateway_deployment.deployment.id
    rest_api_id   = aws_api_gateway_rest_api.rers_api.id
    stage_name    = "prod"

    xray_tracing_enabled = true

    lifecycle {
        ignore_changes = [stage_name]
    }
}

resource "aws_lambda_permission" "apigw_invoke" {
    statement_id  = "AllowAPIGatewayInvoke"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.record_event_lambda.function_name
    principal     = "apigateway.amazonaws.com"
    source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.rers_api.id}/*/POST/event"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "bucket" {
    bucket = "my-private-bucket-fddse334"
}

resource "aws_dynamodb_table" "table" {
    name           = "my-private-table"
    billing_mode   = "PAY_PER_REQUEST"
    hash_key       = "id"

    attribute {
        name = "id"
        type = "S"
    }
}
