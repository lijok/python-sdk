import typing

from python_sdk.metrics import _metrics_backend
from python_sdk.metrics._metrics_backend_factory import _aws_cloudwatch_config

MetricsBackendConfig: typing.TypeAlias = _aws_cloudwatch_config.AWSCloudWatchConfig


def get_metrics_backend(config: MetricsBackendConfig) -> _metrics_backend.MetricsBackend:
    if isinstance(config, _aws_cloudwatch_config.AWSCloudWatchConfig):
        return _aws_cloudwatch(config=config)
    raise NotImplementedError(type(config))


def _aws_cloudwatch(config: _aws_cloudwatch_config.AWSCloudWatchConfig) -> _metrics_backend.MetricsBackend:
    import python_sdk.metrics._metrics_backend._aws_cloudwatch

    return python_sdk.metrics._metrics_backend._aws_cloudwatch.AWSCloudWatchMetricsBackend(**config.as_dict)
