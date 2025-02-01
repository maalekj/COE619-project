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

resource "aws_api_gateway_method" "get_event" {
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
  timeout       = 30

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.event_topic.arn
    }
  }
}

resource "aws_lambda_function" "event_validate_lambda" {
    function_name = "event_validate_lambda"
    handler       = "event_validate_lambda.lambda_handler"
    runtime       = "python3.8"
    role          = aws_iam_role.lambda_exec.arn
    filename      = "event_validate_lambda.zip"
    source_code_hash = filebase64sha256("event_validate_lambda.zip")
    timeout =  30
}

resource "aws_lambda_function" "get_event_lambda" {
  function_name = "get_event_lambda"
  handler       = "get_event_lambda.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "get_event_lambda.zip"
  source_code_hash = filebase64sha256("get_event_lambda.zip")
  timeout       = 30

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.my_private_table.name
    }
  }
}

resource "aws_lambda_function" "register_edge_point_lambda" {
  function_name = "register_edge_point"
  handler       = "register_edge_point.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "register_edge_point.zip"
  source_code_hash = filebase64sha256("register_edge_point.zip")
  timeout       = 30

  environment {
    variables = {
      EDGE_NODE_TABLE_NAME = aws_dynamodb_table.edge_node_table.name
    }
  }
}

resource "aws_lambda_function" "get_edge_node_lambda" {
  function_name = "get_edge_node"
  handler       = "get_edge_node.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "get_edge_node.zip"
  source_code_hash = filebase64sha256("get_edge_node.zip")
  timeout       = 30

  environment {
    variables = {
      EDGE_NODE_TABLE_NAME = aws_dynamodb_table.edge_node_table.name
    }
  }
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
    name        = "lambda_dynamodb_policy"
    description = "IAM policy for Lambda to access DynamoDB"
    policy      = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:GetItem",
                    "dynamodb:Scan",
                    "dynamodb:Query"
                ]
                Resource = aws_dynamodb_table.edge_node_table.arn
            }
        ]
    })
}

resource "aws_iam_policy" "lambda_invoke_policy" {
    name        = "lambda_invoke_policy"
    description = "IAM policy for Lambda to invoke other Lambda functions"
    policy      = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "lambda:InvokeFunction"
                ]
                Resource = "arn:aws:lambda:me-south-1:354918372412:function:event_validate_lambda"
            }
        ]
    })
}

resource "aws_iam_policy" "lambda_ssm_policy" {
    name        = "lambda_ssm_policy"
    description = "IAM policy for Lambda to access SSM Parameter Store"
    policy      = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Effect = "Allow",
                Action = [
                    "ssm:GetParameter"
                ],
                Resource = "arn:aws:ssm:me-south-1:${data.aws_caller_identity.current.account_id}:parameter/openai/api_key"
            }
        ]
    })
}

resource "aws_iam_policy" "lambda_sns_publish_policy" {
  name        = "lambda_sns_publish_policy"
  description = "IAM policy for Lambda to publish to SNS"
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "sns:Publish",
        Resource = aws_sns_topic.event_topic.arn
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_dynamodb_access_policy" {
  name        = "lambda_dynamodb_access_policy"
  description = "IAM policy for Lambda to access DynamoDB"
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "dynamodb:GetItem",
          "dynamodb:Query"
        ],
        Resource = aws_dynamodb_table.my_private_table.arn
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

resource "aws_iam_role_policy_attachment" "lambda_invoke_policy_attachment" {
    role       = aws_iam_role.lambda_exec.name
    policy_arn = aws_iam_policy.lambda_invoke_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
    role       = aws_iam_role.lambda_exec.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_ssm_policy_attachment" {
    role       = aws_iam_role.lambda_exec.name
    policy_arn = aws_iam_policy.lambda_ssm_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_sns_publish_policy_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_sns_publish_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_access_policy_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_dynamodb_access_policy.arn
}

resource "aws_api_gateway_integration" "get_event_integration" {
    rest_api_id             = aws_api_gateway_rest_api.rers_api.id
    resource_id             = aws_api_gateway_resource.event_resource.id
    http_method             = aws_api_gateway_method.get_event.http_method
    type                    = "AWS_PROXY"
    integration_http_method = "POST"
    uri                     = aws_lambda_function.get_event_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "post_event_integration" {
    rest_api_id             = aws_api_gateway_rest_api.rers_api.id
    resource_id             = aws_api_gateway_resource.event_resource.id
    http_method             = aws_api_gateway_method.post_event.http_method
    type                    = "AWS_PROXY"
    integration_http_method = "POST"
    uri                     = aws_lambda_function.record_event_lambda.invoke_arn
}

resource "aws_api_gateway_resource" "edge_node_resource" {
  rest_api_id = aws_api_gateway_rest_api.rers_api.id
  parent_id   = aws_api_gateway_rest_api.rers_api.root_resource_id
  path_part   = "edge-node"
}

resource "aws_api_gateway_method" "post_edge_node" {
  rest_api_id   = aws_api_gateway_rest_api.rers_api.id
  resource_id   = aws_api_gateway_resource.edge_node_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "get_edge_node" {
  rest_api_id   = aws_api_gateway_rest_api.rers_api.id
  resource_id   = aws_api_gateway_resource.edge_node_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "register_edge_point_integration" {
  rest_api_id             = aws_api_gateway_rest_api.rers_api.id
  resource_id             = aws_api_gateway_resource.edge_node_resource.id
  http_method             = aws_api_gateway_method.post_edge_node.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.register_edge_point_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "get_edge_node_integration" {
  rest_api_id             = aws_api_gateway_rest_api.rers_api.id
  resource_id             = aws_api_gateway_resource.edge_node_resource.id
  http_method             = aws_api_gateway_method.get_edge_node.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.get_edge_node_lambda.invoke_arn
}

resource "aws_api_gateway_deployment" "deployment" {
    rest_api_id = aws_api_gateway_rest_api.rers_api.id
    depends_on  = [
      aws_api_gateway_integration.get_event_integration,
      aws_api_gateway_integration.post_event_integration,
      aws_api_gateway_integration.register_edge_point_integration,
      aws_api_gateway_integration.get_edge_node_integration
    ]
    description = "Deployment for RERS API"
}

resource "aws_api_gateway_stage" "prod" {
  stage_name    = "prod"
  rest_api_id   = aws_api_gateway_rest_api.rers_api.id
  deployment_id = aws_api_gateway_deployment.deployment.id

  xray_tracing_enabled = true

}

resource "aws_lambda_permission" "apigw_invoke" {
    statement_id  = "AllowAPIGatewayInvoke"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.record_event_lambda.function_name
    principal     = "apigateway.amazonaws.com"
    source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.rers_api.id}/*/POST/event"
}

resource "aws_lambda_permission" "allow_sns_publish" {
  statement_id  = "AllowSNSPublish"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.record_event_lambda.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.event_topic.arn
}

resource "aws_lambda_permission" "allow_api_gateway_invoke_get_event" {
    statement_id  = "AllowAPIGatewayInvokeGetEventReport"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.get_event_lambda.function_name
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_api_gateway_rest_api.rers_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_invoke_register_edge_point" {
  statement_id  = "AllowAPIGatewayInvokeRegisterEdgePoint"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.register_edge_point_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.rers_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_invoke_get_edge_node" {
  statement_id  = "AllowAPIGatewayInvokeGetEdgeNode"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_edge_node_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.rers_api.execution_arn}/*/*"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "bucket" {
    bucket = "my-private-bucket-fddse334"
}

resource "aws_dynamodb_table" "my_private_table" {
    name           = "my-private-table"
    billing_mode   = "PAY_PER_REQUEST"
    hash_key       = "id"

    attribute {
        name = "id"
        type = "S"
    }
}

resource "aws_dynamodb_table" "edge_node_table" {
  name           = "EdgeNodeTable"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "node_id"

  attribute {
    name = "node_id"
    type = "S"
  }
}

resource "aws_sns_topic" "event_topic" {
  name = "event_topic"
}
