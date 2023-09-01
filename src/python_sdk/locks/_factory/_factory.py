import typing

from python_sdk.locks import _lock_provider
from python_sdk.locks._factory import _aws_dynamodb_config
from python_sdk.locks._factory import _s3_config

LockProviderConfig: typing.TypeAlias = _s3_config.S3Config | _aws_dynamodb_config.AWSDynamoDBConfig


def get_lock_provider(config: LockProviderConfig) -> _lock_provider.LockProvider:
    if isinstance(config, _s3_config.S3Config):
        return _s3(config=config)
    if isinstance(config, _aws_dynamodb_config.AWSDynamoDBConfig):
        return _aws_dynamodb(config=config)
    raise NotImplementedError(type(config))


def _s3(config: _s3_config.S3Config) -> _lock_provider.LockProvider:
    import python_sdk.locks._lock_provider._s3

    return python_sdk.locks._lock_provider._s3.S3LockProvider(**config.as_dict)


def _aws_dynamodb(config: _aws_dynamodb_config.AWSDynamoDBConfig) -> _lock_provider.LockProvider:
    import python_sdk.locks._lock_provider._aws_dynamodb

    return python_sdk.locks._lock_provider._aws_dynamodb.AWSDynamoDBLockProvider(**config.as_dict)
