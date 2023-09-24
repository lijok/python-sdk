import typing

from python_sdk.service import _app


class Config:
    app: _app.App

    def __init__(
        self,
        app: _app.App,
    ):
        self.app = app

    @property
    def as_dict(self) -> dict[str, typing.Any]:
        return {
            "app": self.app,
        }
