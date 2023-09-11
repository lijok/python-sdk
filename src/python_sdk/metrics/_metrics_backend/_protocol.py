from __future__ import annotations

import typing

ObjectType: typing.TypeAlias = str | dict[str, typing.Any]


class MetricsBackend(typing.Protocol):
    def counter(self, name: str) -> MetricCounter:
        ...


class MetricCounter:
    def add(self, value: float | int, **dimensions: str) -> None:
        ...
