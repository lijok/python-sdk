import json
import typing
import uuid

import boto3  # type: ignore
import pytest

from python_sdk import secrets


@pytest.fixture(scope="function")
def configure_aws_sm_secrets_engine(localstack: None) -> None:
    secrets.SecretsConfig.set_config_value(option="ENGINE", value="AWS_SECRETS_MANAGER")
    secrets.AWSSecretsEngineConfig.set_config_value(option="ACCESS_KEY_ID", value="fake")
    secrets.AWSSecretsEngineConfig.set_config_value(option="SECRET_ACCESS_KEY", value="fake")
    secrets.AWSSecretsEngineConfig.set_config_value(option="SESSION_TOKEN", value="fake")
    secrets.AWSSecretsEngineConfig.set_config_value(option="REGION_NAME", value="eu-west-1")
    secrets.AWSSecretsEngineConfig.set_config_value(option="USE_SSL", value=False)
    secrets.AWSSecretsEngineConfig.set_config_value(option="VERIFY", value=False)
    secrets.AWSSecretsEngineConfig.set_config_value(option="ENDPOINT_URL", value="http://localhost:4566")


@pytest.fixture(scope="function")
def configure_aws_ps_secrets_engine(localstack: None) -> None:
    secrets.SecretsConfig.set_config_value(option="ENGINE", value="AWS_SYSTEMS_MANAGER_PARAMETER_STORE")
    secrets.AWSSecretsEngineConfig.set_config_value(option="ACCESS_KEY_ID", value="fake")
    secrets.AWSSecretsEngineConfig.set_config_value(option="SECRET_ACCESS_KEY", value="fake")
    secrets.AWSSecretsEngineConfig.set_config_value(option="SESSION_TOKEN", value="fake")
    secrets.AWSSecretsEngineConfig.set_config_value(option="REGION_NAME", value="eu-west-1")
    secrets.AWSSecretsEngineConfig.set_config_value(option="USE_SSL", value=False)
    secrets.AWSSecretsEngineConfig.set_config_value(option="VERIFY", value=False)
    secrets.AWSSecretsEngineConfig.set_config_value(option="ENDPOINT_URL", value="http://localhost:4566")


@pytest.fixture(scope="function")
def aws_sm_client(configure_aws_sm_secrets_engine: None) -> typing.Any:
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
def aws_ps_client(configure_aws_ps_secrets_engine: None) -> typing.Any:
    return boto3.client(
        service_name="ssm",
        aws_access_key_id="fake",
        aws_secret_access_key="fake",
        aws_session_token="fake",
        region_name="eu-west-1",
        use_ssl=False,
        verify=False,
        endpoint_url="http://localhost:4566",
    )


@pytest.fixture(scope="function")
def random_aws_sm_secret_string(aws_sm_client: typing.Any) -> typing.Generator[tuple[str, str], None, None]:
    name, value = str(uuid.uuid4()), str(uuid.uuid4())
    response = aws_sm_client.create_secret(Name=name, SecretString=value)
    yield name, value
    aws_sm_client.delete_secret(SecretId=response["ARN"], RecoveryWindowInDays=0, ForceDeleteWithoutRecovery=True)


@pytest.fixture(scope="function")
def random_aws_sm_secret_binary(aws_sm_client: typing.Any) -> typing.Generator[tuple[str, str], None, None]:
    name, value = str(uuid.uuid4()), str(uuid.uuid4())
    response = aws_sm_client.create_secret(Name=name, SecretBinary=value.encode("utf-8"))
    yield name, value
    aws_sm_client.delete_secret(SecretId=response["ARN"], RecoveryWindowInDays=0, ForceDeleteWithoutRecovery=True)


@pytest.fixture(scope="function")
def random_aws_sm_secret_json(aws_sm_client: typing.Any) -> typing.Generator[tuple[str, dict[str, str]], None, None]:
    name, value = str(uuid.uuid4()), {str(uuid.uuid4()): str(uuid.uuid4())}
    response = aws_sm_client.create_secret(Name=name, SecretString=json.dumps(value))
    yield name, value
    aws_sm_client.delete_secret(SecretId=response["ARN"], RecoveryWindowInDays=0, ForceDeleteWithoutRecovery=True)


@pytest.fixture(scope="function")
def random_aws_ps_secret_string(aws_ps_client: typing.Any) -> typing.Generator[tuple[str, str], None, None]:
    name, value = str(uuid.uuid4()), str(uuid.uuid4())
    aws_ps_client.put_parameter(Name=name, Value=value, Type="String")
    yield name, value
    aws_ps_client.delete_parameter(Name=name)


@pytest.fixture(scope="function")
def random_aws_ps_secret_string_list(aws_ps_client: typing.Any) -> typing.Generator[tuple[str, list[str]], None, None]:
    name, value = str(uuid.uuid4()), [str(uuid.uuid4()), str(uuid.uuid4())]
    aws_ps_client.put_parameter(Name=name, Value=",".join(value), Type="StringList")
    yield name, value
    aws_ps_client.delete_parameter(Name=name)


@pytest.fixture(scope="function")
def random_aws_ps_secret_json(aws_ps_client: typing.Any) -> typing.Generator[tuple[str, dict[str, str]], None, None]:
    name, value = str(uuid.uuid4()), {str(uuid.uuid4()): str(uuid.uuid4())}
    aws_ps_client.put_parameter(Name=name, Value=json.dumps(value), Type="String")
    yield name, value
    aws_ps_client.delete_parameter(Name=name)
