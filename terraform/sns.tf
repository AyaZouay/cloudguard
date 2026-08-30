resource "aws_sns_topic" "anomaly_alerts" {
  name = "${var.project_name}-${var.environment}-anomaly-alerts"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.anomaly_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}