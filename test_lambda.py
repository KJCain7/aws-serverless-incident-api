
import json
from unittest.mock import patch, MagicMock

from src import lambda_function
from src.lambda_function import lambda_handler

def make_event(payload):
    return {"body": json.dumps(payload)}


valid_incident = {
    "title": "Website unavailable",
    "description": "The company website returns HTTP 503 errors.",
    "severity": "high",
    "reporter": "Kyle",
}



def test_valid_incident():
    mock_table = MagicMock()

    with patch.object(lambda_function, "TABLE_NAME", "test-incidents"), \
         patch("boto3.resource") as mock_resource:

        mock_resource.return_value.Table.return_value = mock_table

        result = lambda_handler(make_event(valid_incident), None)

    assert result["statusCode"] == 201

    body = json.loads(result["body"])
    assert body["incident"]["title"] == "Website unavailable"
    assert body["incident"]["severity"] == "high"
    assert body["incident"]["status"] == "open"
    assert body["incident"]["incidentId"]

    mock_table.put_item.assert_called_once()


def test_invalid_severity():
    payload = {**valid_incident, "severity": "urgent"}

    result = lambda_handler(make_event(payload), None)

    assert result["statusCode"] == 400


def test_missing_body():
    result = lambda_handler({}, None)

    assert result["statusCode"] == 400


def test_health_check():
    result = lambda_handler({"rawPath": "/health"}, None)

    assert result["statusCode"] == 200


def test_missing_table_configuration():
    with patch.object(lambda_function, "TABLE_NAME", None):
        result = lambda_handler(make_event(valid_incident), None)

    assert result["statusCode"] == 500
    body = json.loads(result["body"])
    assert body["error"] == "Incident storage is not configured"


def test_database_failure():
    mock_table = MagicMock()
    mock_table.put_item.side_effect = RuntimeError("Simulated database failure")

    with patch.object(lambda_function, "TABLE_NAME", "test-incidents"), \
         patch("boto3.resource") as mock_resource:

        mock_resource.return_value.Table.return_value = mock_table
        result = lambda_handler(make_event(valid_incident), None)

    assert result["statusCode"] == 500
    body = json.loads(result["body"])
    assert body["error"] == "Could not save incident"


if __name__ == "__main__":
    for test in (
        test_valid_incident,
        test_invalid_severity,
        test_missing_body,
        test_health_check,
        test_missing_table_configuration,
        test_database_failure,
    ):
        test()
        print(f"PASS: {test.__name__}")

    print("All tests passed.")
