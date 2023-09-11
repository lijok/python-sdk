from __future__ import annotations

import typing
import uuid

import pytest

if typing.TYPE_CHECKING:
    import mypy_boto3_cloudwatch

from python_sdk import metrics

MetricsBackendType: typing.TypeAlias = typing.Literal["AWS_CLOUDWATCH"]


@pytest.fixture(scope="function", params=typing.get_args(MetricsBackendType), ids=typing.get_args(MetricsBackendType))
def metrics_backend(
    request: pytest.FixtureRequest,
    metrics_backend_aws_cloudwatch: metrics.MetricsBackend,
) -> metrics.MetricsBackend:
    requested_type: MetricsBackendType = request.param
    if requested_type == "AWS_CLOUDWATCH":
        return metrics_backend_aws_cloudwatch
    raise NotImplementedError(requested_type)


@pytest.fixture(scope="function", autouse=False)
def metrics_backend_aws_cloudwatch(
    aws_cloudwatch_client: mypy_boto3_cloudwatch.CloudWatchClient, namespace_for_aws_cloudwatch_metrics_backend: str
) -> typing.Generator[metrics.MetricsBackend, None, None]:
    yield metrics.get_metrics_backend(
        config=metrics.AWSCloudWatchConfig(
            aws_cloudwatch_client=aws_cloudwatch_client,
            namespace=namespace_for_aws_cloudwatch_metrics_backend,
        )
    )


@pytest.fixture(scope="function", autouse=False)
def namespace_for_aws_cloudwatch_metrics_backend() -> str:
    return str(uuid.uuid4())
