from __future__ import annotations

import dataclasses
import datetime
import typing

if typing.TYPE_CHECKING:
    import mypy_boto3_dynamodb


@dataclasses.dataclass(frozen=True)
class AWSDynamoDBConfig:
    hostname: str | None
    default_ttl: datetime.timedelta
    default_metadata: dict[str, str]
    default_retry_times: int
    default_retry_delay: datetime.timedelta
    aws_dynamodb_client: mypy_boto3_dynamodb.DynamoDBClient
    table_name: str
    object_key: str
    partition_key: str
    sort_key: str | None = None

    @property
    def as_dict(self) -> AWSDynamoDBConfigDict:
        return self.__dict__  # type: ignore


class AWSDynamoDBConfigDict(typing.TypedDict):
    hostname: str | None
    default_ttl: datetime.timedelta
    default_metadata: dict[str, str]
    default_retry_times: int
    default_retry_delay: datetime.timedelta
    aws_dynamodb_client: mypy_boto3_dynamodb.DynamoDBClient
    table_name: str
    partition_key: str
    object_key: str
