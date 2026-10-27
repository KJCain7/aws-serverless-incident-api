import json
import os
import uuid
from datetime import datetime, timezone

import boto3


ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}

MAX_TITLE_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 2000
MAX_REPORTER_LENGTH = 100

TABLE_NAME = os.environ.get("INCIDENTS_TABLE")
dynamodb = None

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):

    if (
    event.get("routeKey") == "GET /health"
    or event.get("rawPath") == "/health"
):
        return response(200, {"status": "ok"})

    raw_body = event.get("body")

    if not raw_body:
        return response(400, {"error": "Request body is required"})

    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, TypeError):
        return response(400, {"error": "Request body must be valid JSON"})

    if not isinstance(payload, dict):
        return response(400, {"error": "JSON body must be an object"})

    title = payload.get("title")
    description = payload.get("description")
    severity = payload.get("severity")
    reporter = payload.get("reporter")

    if not all(isinstance(value, str) for value in (
        title, description, severity, reporter
    )):
        return response(400, {
            "error": "title, description, severity and reporter must be strings"
        })

    title = title.strip()
    description = description.strip()
    severity = severity.strip().lower()
    reporter = reporter.strip()

    if not title or len(title) > 120:
        return response(400, {"error": "Title must contain 1-120 characters"})

    if not description or len(description) > 2000:
        return response(400, {
            "error": "Description must contain 1-2000 characters"
        })

    if severity not in ALLOWED_SEVERITIES:
        return response(400, {
            "error": "Severity must be low, medium, high or critical"
        })

    if not reporter or len(reporter) > 100:
        return response(400, {
            "error": "Reporter must contain 1-100 characters"
        })

    incident = {
        "incidentId": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "severity": severity,
        "reporter": reporter,
        "status": "open",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    
    if not TABLE_NAME:
        return response(500, {
            "error": "Incident storage is not configured"
        })

    
    if not TABLE_NAME:
        return response(500, {
            "error": "Incident storage is not configured"
        })

    try:
        table = boto3.resource("dynamodb").Table(TABLE_NAME)
        table.put_item(Item=incident)
    except Exception:
        print("ERROR: Failed to save incident to DynamoDB")
        return response(500, {
            "error": "Could not save incident"
        })

    return response(201, {
        "message": "Incident created successfully",
        "incident": incident,
    })
