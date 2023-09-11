from __future__ import annotations

import asyncio
import datetime
import logging
import typing

if typing.TYPE_CHECKING:
    import mypy_boto3_cloudwatch


# TODO: Cleanup background tasks at exit
class AWSCloudWatchMetricsBackend:
    aws_cloudwatch_client: mypy_boto3_cloudwatch.CloudWatchClient
    namespace: str

    def __init__(self, aws_cloudwatch_client: mypy_boto3_cloudwatch.CloudWatchClient, namespace: str) -> None:
        self.aws_cloudwatch_client = aws_cloudwatch_client
        self.namespace = namespace

    def counter(self, name: str) -> AWSCloudWatchMetricCounter:
        return AWSCloudWatchMetricCounter(
            aws_cloudwatch_client=self.aws_cloudwatch_client,
            namespace=self.namespace,
            name=name,
        )


class AWSCloudWatchMetricCounter:
    aws_cloudwatch_client: mypy_boto3_cloudwatch.CloudWatchClient
    namespace: str
    name: str
    _background_tasks: set[asyncio.Task[None]] = set()

    def __init__(
        self, aws_cloudwatch_client: mypy_boto3_cloudwatch.CloudWatchClient, namespace: str, name: str
    ) -> None:
        self.aws_cloudwatch_client = aws_cloudwatch_client
        self.namespace = namespace
        self.name = name
        self._background_tasks = set()

    def add(self, value: float | int, **dimensions: str) -> None:
        self._schedule_task(
            self._write(
                namespace=self.namespace,
                metric_name=self.name,
                dimensions=dimensions,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
                value=value,
            )
        )

    def _schedule_task(self, coroutine: typing.Coroutine[None, None, None]) -> asyncio.Task[None]:
        task = asyncio.create_task(coroutine)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    async def _write(
        self,
        namespace: str,
        metric_name: str,
        dimensions: dict[str, str],
        timestamp: datetime.datetime,
        value: float | int,
    ) -> None:
        try:
            self.aws_cloudwatch_client.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Dimensions": [{"Name": key, "Value": val} for key, val in dimensions.items()],
                        "Timestamp": timestamp,
                        "Value": value,
                    }
                ],
            )
        except Exception:
            logging.exception("Metrics publish failed")
