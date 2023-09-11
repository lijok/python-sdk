import typing


class SyncCallback(typing.Protocol):
    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        ...


class AsyncCallback(typing.Protocol):
    async def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        ...


Callback: typing.TypeAlias = SyncCallback | AsyncCallback
