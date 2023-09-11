from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    import mypy_boto3_cloudwatch


@dataclasses.dataclass(frozen=True)
class AWSCloudWatchConfig:
    aws_cloudwatch_client: mypy_boto3_cloudwatch.CloudWatchClient
    namespace: str

    @property
    def as_dict(self) -> AWSCloudWatchConfigDict:
        return self.__dict__  # type: ignore


class AWSCloudWatchConfigDict(typing.TypedDict):
    aws_cloudwatch_client: mypy_boto3_cloudwatch.CloudWatchClient
    namespace: str
