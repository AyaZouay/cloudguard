# Zip up the Lambda source code automatically whenever it changes
data "archive_file" "anomaly_detector_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/anomaly_detector/handler.py"
  output_path = "${path.module}/../lambda/anomaly_detector/handler.zip"
}

resource "aws_lambda_function" "anomaly_detector" {
  function_name = "${var.project_name}-${var.environment}-anomaly-detector"
  role          = aws_iam_role.lambda_exec_role.arn

  filename         = data.archive_file.anomaly_detector_zip.output_path
  source_code_hash = data.archive_file.anomaly_detector_zip.output_base64sha256

  handler = "handler.handler"
  runtime = "python3.12"
  timeout = 30

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
      SNS_TOPIC_ARN    = aws_sns_topic.anomaly_alerts.arn
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Allow CloudWatch Logs to invoke this Lambda
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.anomaly_detector.function_name
  principal     = "logs.${var.aws_region}.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.app_logs.arn}:*"
}

# The actual trigger: whenever new logs land, invoke the Lambda
resource "aws_cloudwatch_log_subscription_filter" "anomaly_trigger" {
  name            = "${var.project_name}-${var.environment}-anomaly-trigger"
  log_group_name  = aws_cloudwatch_log_group.app_logs.name
  filter_pattern  = ""
  destination_arn = aws_lambda_function.anomaly_detector.arn

  depends_on = [aws_lambda_permission.allow_cloudwatch]
}