from __future__ import annotations

import datetime
import typing
import uuid

import mypy_boto3_dynamodb
import pytest

if typing.TYPE_CHECKING:
    import mypy_boto3_s3

from python_sdk import locks

LockProviderType: typing.TypeAlias = typing.Literal["S3", "AWS_DYNAMODB"]


@pytest.fixture(scope="function", params=typing.get_args(LockProviderType), ids=typing.get_args(LockProviderType))
def lock_provider(
    request: pytest.FixtureRequest,
    lock_provider_s3: locks.LockProvider,
    lock_provider_aws_dynamodb: locks.LockProvider,
) -> locks.LockProvider:
    requested_type: LockProviderType = request.param
    if requested_type == "S3":
        return lock_provider_s3
    if requested_type == "AWS_DYNAMODB":
        return lock_provider_aws_dynamodb
    raise NotImplementedError(requested_type)


@pytest.fixture(scope="function", autouse=False)
def lock_provider_s3(
    aws_s3_client: mypy_boto3_s3.S3Client,
    s3_bucket_for_s3_lock_provider: str,
) -> typing.Generator[locks.LockProvider, None, None]:
    yield locks.get_lock_provider(
        config=locks.S3Config(
            hostname=None,
            default_ttl=datetime.timedelta(seconds=10),
            default_metadata={},
            default_retry_times=0,
            default_retry_delay=datetime.timedelta(seconds=0),
            s3_client=aws_s3_client,
            bucket_name=s3_bucket_for_s3_lock_provider,
            lock_key_prefix="",
        )
    )


@pytest.fixture(scope="function", autouse=False)
def lock_provider_aws_dynamodb(
    aws_dynamodb_client: mypy_boto3_dynamodb.DynamoDBClient,
    aws_dynamodb_table_for_aws_dynamodb_lock_provider: str,
) -> typing.Generator[locks.LockProvider, None, None]:
    yield locks.get_lock_provider(
        config=locks.AWSDynamoDBConfig(
            hostname=None,
            default_ttl=datetime.timedelta(seconds=10),
            default_metadata={},
            default_retry_times=0,
            default_retry_delay=datetime.timedelta(seconds=0),
            aws_dynamodb_client=aws_dynamodb_client,
            table_name=aws_dynamodb_table_for_aws_dynamodb_lock_provider,
            partition_key="LockID",
            object_key="state",
        )
    )


@pytest.fixture(scope="session", autouse=False)
def s3_bucket_for_s3_lock_provider(aws_s3_client: mypy_boto3_s3.S3Client) -> typing.Generator[str, None, None]:
    bucket_name = str(uuid.uuid4())
    aws_s3_client.create_bucket(Bucket=bucket_name)
    yield bucket_name
    while True:
        response = aws_s3_client.list_objects_v2(Bucket=bucket_name)
        if keys := [content["Key"] for content in response.get("Contents", [])]:
            aws_s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": [{"Key": key} for key in keys]})
        else:
            break
    aws_s3_client.delete_bucket(Bucket=bucket_name)


# @pytest.fixture(scope="function", autouse=True)
# def clear_s3_bucket_for_s3_lock_provider(
#     aws_s3_client: mypy_boto3_s3.S3Client,
#     s3_bucket_for_s3_lock_provider: str,
# ) -> typing.Generator[None, None, None]:
#     yield
#     while True:
#         response = aws_s3_client.list_objects_v2(Bucket=s3_bucket_for_s3_lock_provider)
#         if keys := [content["Key"] for content in response.get("Contents", [])]:
#             aws_s3_client.delete_objects(
#                 Bucket=s3_bucket_for_s3_lock_provider, Delete={"Objects": [{"Key": key} for key in keys]}
#             )
#         else:
#             break


@pytest.fixture(scope="session", autouse=True)
def aws_dynamodb_table_for_aws_dynamodb_lock_provider(
    aws_dynamodb_client: mypy_boto3_dynamodb.DynamoDBClient,
) -> typing.Generator[str, None, None]:
    table_name = str(uuid.uuid4())
    aws_dynamodb_client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {
                "AttributeName": "LockID",
                "AttributeType": "S",
            }
        ],
        KeySchema=[
            {
                "AttributeName": "LockID",
                "KeyType": "HASH",
            }
        ],
        BillingMode="PAY_PER_REQUEST",
        SSESpecification={
            "Enabled": True,
            "SSEType": "AES256",
        },
        TableClass="STANDARD",
        DeletionProtectionEnabled=False,
    )
    yield table_name
    aws_dynamodb_client.delete_table(TableName=table_name)


@pytest.fixture(scope="function", autouse=False)
def lock_key() -> str:
    return str(uuid.uuid4())
