from __future__ import annotations

import json
import typing

import boto3
import pytest

if typing.TYPE_CHECKING:
    import mypy_boto3_s3
    import mypy_boto3_dynamodb
    import mypy_boto3_cloudwatch

from python_sdk import bin

LOCALSTACK_ENDPOINT_URL: str = "http://localhost:4566"
AWS_ACCESS_KEY_ID: str = "FAKE"
AWS_SECRET_ACCESS_KEY: str = "FAKE"
AWS_SESSION_TOKEN: str = "FAKE"
REGION_NAME: str = "us-east-1"
USE_SSL: bool = False
VERIFY: bool = False


@pytest.fixture(scope="session", autouse=False)
def running_docker_containers() -> list[str]:
    response = bin.call("docker", "ps", "--format", "{{json .}}")
    containers = [json.loads(container) for container in response.strip().splitlines()]
    return [container["Names"] for container in containers]


@pytest.fixture(scope="session", autouse=True)
def localstack(running_docker_containers: list[str]) -> typing.Generator[None, None, None]:
    if "localstack_main" in running_docker_containers:
        # Localstack was started manually. We're not starting/stopping it.
        yield
        return

    try:
        bin.call("docker", "compose", "up", "--wait", "localstack")
        yield
    finally:
        bin.call("docker", "compose", "down")


@pytest.fixture(scope="session", autouse=False)
def boto3_session(localstack: None) -> boto3.Session:
    return boto3.Session(
        aws_access_key_id="FAKE",
        aws_secret_access_key="FAKE",
        aws_session_token="FAKE",
        region_name="us-east-1",
    )


@pytest.fixture(scope="session", autouse=False)
def aws_s3_client(boto3_session: boto3.Session) -> mypy_boto3_s3.S3Client:
    return boto3_session.client(
        service_name="s3",
        use_ssl=USE_SSL,
        verify=VERIFY,
        endpoint_url=LOCALSTACK_ENDPOINT_URL,
    )


@pytest.fixture(scope="session", autouse=False)
def aws_dynamodb_client(boto3_session: boto3.Session) -> mypy_boto3_dynamodb.DynamoDBClient:
    return boto3_session.client(
        service_name="dynamodb",
        use_ssl=USE_SSL,
        verify=VERIFY,
        endpoint_url=LOCALSTACK_ENDPOINT_URL,
    )


@pytest.fixture(scope="session", autouse=False)
def aws_cloudwatch_client(boto3_session: boto3.Session) -> mypy_boto3_cloudwatch.CloudWatchClient:
    return boto3_session.client(
        service_name="cloudwatch",
        use_ssl=USE_SSL,
        verify=VERIFY,
        endpoint_url=LOCALSTACK_ENDPOINT_URL,
    )
