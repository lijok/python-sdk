import datetime
import typing

from python_sdk.service import _app


class Config:
    app: _app.App
    run_for: datetime.timedelta | None
    tick_interval: datetime.timedelta

    def __init__(
        self,
        app: _app.App,
        run_for: datetime.timedelta | None = None,
    ):
        self.app = app
        self.run_for = run_for
        self.tick_interval = datetime.timedelta(seconds=0.1)

    @property
    def as_dict(self) -> dict[str, typing.Any]:
        return {"app": self.app, "run_for": self.run_for, "tick_interval": self.tick_interval}
