variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-west-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to use for authentication"
  type        = string
  default     = "cloudguard-terraform"
}

variable "project_name" {
  description = "Name used to prefix/tag all resources"
  type        = string
  default     = "cloudguard"
}

variable "environment" {
  description = "Deployment environment (e.g. dev, prod)"
  type        = string
  default     = "dev"
}

variable "alert_email" {
  description = "Email address to receive SNS anomaly alerts"
  type        = string
}

variable "bedrock_model_id" {
  description = "Bedrock model ID used for anomaly detection"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}