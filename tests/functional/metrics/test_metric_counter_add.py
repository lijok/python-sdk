from python_sdk import metrics


class TestMetricCounterAdd:
    async def test_can_add(self, metrics_backend: metrics.MetricsBackend) -> None:
        counter = metrics_backend.counter(name="test")
        counter.add(1.0)

    async def test_can_add_with_dimensions(self, metrics_backend: metrics.MetricsBackend) -> None:
        counter = metrics_backend.counter(name="test")
        counter.add(1.0, URL="test")

    async def test_can_add_with_kwargs_dimensions(self, metrics_backend: metrics.MetricsBackend) -> None:
        counter = metrics_backend.counter(name="test")
        counter.add(1.0, **{"service.url": "test"})
