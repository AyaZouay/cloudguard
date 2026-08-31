"""
CloudGuard anomaly detector Lambda.

Triggered automatically by a CloudWatch Logs subscription filter.
For each incoming log event, asks Claude (via Bedrock) whether it looks
anomalous. If so, publishes an alert to the SNS topic.
"""

import base64
import gzip
import json
import os
import boto3

REGION = os.environ["AWS_REGION"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)


def decode_log_payload(event):
    """CloudWatch Logs subscription events arrive base64-encoded and gzipped."""
    compressed_payload = base64.b64decode(event["awslogs"]["data"])
    uncompressed_payload = gzip.decompress(compressed_payload)
    return json.loads(uncompressed_payload)


def ask_bedrock(log_message):
    """Ask Claude whether this log entry looks anomalous."""
    prompt = (
        "You are a log monitoring assistant. Look at this application log "
        "entry and decide if it represents normal behavior or an anomaly "
        "(such as errors, security issues, or unusual patterns).\n\n"
        f"Log entry: {log_message}\n\n"
        "Respond with exactly one line in this format:\n"
        "VERDICT: <NORMAL or ANOMALY> | REASON: <short reason, one sentence>"
    )

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
    )

    response_body = json.loads(response["body"].read())
    return response_body["content"][0]["text"].strip()


def parse_verdict(bedrock_reply):
    """Pull out NORMAL/ANOMALY and the reason from Claude's reply."""
    is_anomaly = "ANOMALY" in bedrock_reply.upper()
    return is_anomaly, bedrock_reply


def send_alert(log_message, reason):
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="CloudGuard: Anomaly Detected",
        Message=(
            f"CloudGuard detected an anomalous log entry.\n\n"
            f"Log: {log_message}\n\n"
            f"Assessment: {reason}"
        ),
    )


def handler(event, context):
    payload = decode_log_payload(event)
    log_events = payload.get("logEvents", [])

    results = []

    for log_event in log_events:
        message = log_event["message"]

        bedrock_reply = ask_bedrock(message)
        is_anomaly, reason = parse_verdict(bedrock_reply)

        print(f"Log: {message} -> {bedrock_reply}")

        if is_anomaly:
            send_alert(message, reason)

        results.append({"message": message, "verdict": bedrock_reply})

    return {"processed": len(results), "results": results}