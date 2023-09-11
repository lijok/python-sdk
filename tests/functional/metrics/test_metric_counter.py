from python_sdk import metrics


async def test_metric_counter_can_be_obtained(metrics_backend: metrics.MetricsBackend) -> None:
    counter = metrics_backend.counter(name="test")
    assert counter


async def test_duplicate_metric_counter_can_be_obtained(metrics_backend: metrics.MetricsBackend) -> None:
    counter = metrics_backend.counter(name="test")
    counter2 = metrics_backend.counter(name="test")
    assert counter
    assert counter2
