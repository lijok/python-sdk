from __future__ import annotations

import dataclasses
import datetime
import typing

if typing.TYPE_CHECKING:
    import mypy_boto3_s3


@dataclasses.dataclass(frozen=True)
class S3Config:
    hostname: str | None
    default_ttl: datetime.timedelta
    default_metadata: dict[str, str]
    default_retry_times: int
    default_retry_delay: datetime.timedelta
    s3_client: mypy_boto3_s3.S3Client
    bucket_name: str
    lock_key_prefix: str

    @property
    def as_dict(self) -> S3ConfigDict:
        return self.__dict__  # type: ignore


class S3ConfigDict(typing.TypedDict):
    hostname: str | None
    default_ttl: datetime.timedelta
    default_metadata: dict[str, str]
    default_retry_times: int
    default_retry_delay: datetime.timedelta
    s3_client: mypy_boto3_s3.S3Client
    bucket_name: str
    lock_key_prefix: str
