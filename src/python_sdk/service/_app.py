import typing


class App(typing.Protocol):
    async def start(self) -> None:
        ...

    async def stop(self) -> None:
        ...
