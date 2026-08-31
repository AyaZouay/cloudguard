"""
CloudGuard log generator.

Writes synthetic application log entries to a CloudWatch log group,
mostly normal traffic with occasional injected anomalies, so the
downstream anomaly detector has real patterns to catch.

"""

import boto3
import random
import time
import uuid
from datetime import datetime, timezone

# ---- Config ----
AWS_PROFILE = "cloudguard-terraform"
AWS_REGION = "us-west-1"
LOG_GROUP_NAME = "/cloudguard-terraform/dev/app-logs"   # must match your Terraform log group name
LOG_STREAM_NAME = "log-generator"
SEND_INTERVAL_SECONDS = 3
ANOMALY_CHANCE = 0.15  # 15% chance any given log entry is anomalous

# ---- Log message pools ----
NORMAL_LOGS = [
    "INFO Request handled successfully, status=200, path=/api/users",
    "INFO User login success, user_id={uid}",
    "INFO Cache hit for key=session:{uid}",
    "INFO Scheduled job completed: daily_report",
    "INFO Request handled successfully, status=200, path=/api/orders",
    "DEBUG Health check passed",
]

ANOMALY_LOGS = [
    "ERROR 500 failed login attempts from IP 10.0.0.5 in the last 30 seconds",
    "ERROR Database connection timeout after 30000ms, retry limit exceeded",
    "WARN Unusual spike in 403 Forbidden responses, 200 in last minute",
    "ERROR Out of memory: Lambda execution terminated unexpectedly",
    "WARN Repeated failed login attempts detected for user_id={uid}, 12 attempts",
    "ERROR API error flood: 89 5xx responses in 60 seconds on /api/payments",
]


def get_log_client():
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return session.client("logs")


def ensure_log_stream(client):
    """Create the log stream if it doesn't already exist."""
    try:
        client.create_log_stream(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=LOG_STREAM_NAME,
        )
    except client.exceptions.ResourceAlreadyExistsException:
        pass  # stream already exists, that's fine


def build_log_message():
    uid = str(uuid.uuid4())[:8]
    if random.random() < ANOMALY_CHANCE:
        message = random.choice(ANOMALY_LOGS).format(uid=uid)
    else:
        message = random.choice(NORMAL_LOGS).format(uid=uid)
    return message


def send_log(client, sequence_token=None):
    message = build_log_message()
    timestamp_ms = int(time.time() * 1000)

    kwargs = {
        "logGroupName": LOG_GROUP_NAME,
        "logStreamName": LOG_STREAM_NAME,
        "logEvents": [
            {"timestamp": timestamp_ms, "message": message}
        ],
    }
    if sequence_token:
        kwargs["sequenceToken"] = sequence_token

    response = client.put_log_events(**kwargs)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Sent: {message}")
    return response.get("nextSequenceToken")


def main():
    client = get_log_client()
    ensure_log_stream(client)

    print(f"Sending logs to {LOG_GROUP_NAME} every {SEND_INTERVAL_SECONDS}s. Press Ctrl+C to stop.")
    sequence_token = None

    try:
        while True:
            sequence_token = send_log(client, sequence_token)
            time.sleep(SEND_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()