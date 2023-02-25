import json
import typing
import uuid

import boto3
import pytest

from python_sdk import secrets


@pytest.fixture(scope="function")
def configure_aws_sm_secrets_engine(docker_compose: None) -> None:
    secrets.Secrets.set_config_value(option="ENGINE", value="AWS_SM")
    secrets.Secrets.set_config_value(option="ENGINE_AWS_SM_SECRET_KEY_ID", value="fake")
    secrets.Secrets.set_config_value(option="ENGINE_AWS_SM_SECRET_ACCESS_KEY", value="fake")
    secrets.Secrets.set_config_value(option="ENGINE_AWS_SM_SESSION_TOKEN", value="fake")
    secrets.Secrets.set_config_value(option="ENGINE_AWS_SM_REGION_NAME", value="eu-west-1")
    secrets.Secrets.set_config_value(option="ENGINE_AWS_SM_USE_SSL", value=False)
    secrets.Secrets.set_config_value(option="ENGINE_AWS_SM_VERIFY", value=False)
    secrets.Secrets.set_config_value(option="ENGINE_AWS_SM_ENDPOINT_URL", value="http://localhost:4566")


@pytest.fixture(scope="function")
def aws_sm_client(configure_aws_sm_secrets_engine: None) -> object:
    return boto3.client(
        service_name="secretsmanager",
        aws_access_key_id="fake",
        aws_secret_access_key="fake",
        aws_session_token="fake",
        region_name="eu-west-1",
        use_ssl=False,
        verify=False,
        endpoint_url="http://localhost:4566",
    )


@pytest.fixture(scope="function")
def random_aws_sm_secret_string(aws_sm_client: object) -> typing.Generator[tuple[str, str], None, None]:
    name, value = str(uuid.uuid4()), str(uuid.uuid4())
    response = aws_sm_client.create_secret(Name=name, SecretString=value)
    yield name, value
    aws_sm_client.delete_secret(SecretId=response["ARN"], RecoveryWindowInDays=0, ForceDeleteWithoutRecovery=True)


@pytest.fixture(scope="function")
def random_aws_sm_secret_binary(aws_sm_client: object) -> typing.Generator[tuple[str, str], None, None]:
    name, value = str(uuid.uuid4()), str(uuid.uuid4())
    response = aws_sm_client.create_secret(Name=name, SecretBinary=value.encode("utf-8"))
    yield name, value
    aws_sm_client.delete_secret(SecretId=response["ARN"], RecoveryWindowInDays=0, ForceDeleteWithoutRecovery=True)


@pytest.fixture(scope="function")
def random_aws_sm_secret_json(aws_sm_client: object) -> typing.Generator[tuple[str, str], None, None]:
    name, value = str(uuid.uuid4()), {str(uuid.uuid4()): str(uuid.uuid4())}
    response = aws_sm_client.create_secret(Name=name, SecretString=json.dumps(value))
    yield name, value
    aws_sm_client.delete_secret(SecretId=response["ARN"], RecoveryWindowInDays=0, ForceDeleteWithoutRecovery=True)
