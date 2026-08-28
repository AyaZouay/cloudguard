# CloudGuard

AI-augmented log anomaly detection pipeline built on AWS.

Synthetic application logs are generated and sent to CloudWatch, analyzed by 
Claude (via AWS Bedrock) for anomalous patterns, and alerts are sent via SNS 
when something looks off. Infrastructure is managed with Terraform and 
deployed via CI/CD. Monitored with Datadog.

## Architecture

(diagram coming soon)

## Stack
- AWS Lambda, CloudWatch, SNS, Bedrock
- Terraform
- GitHub Actions (CI/CD)
- Datadog

## Status
🚧 Work in progress