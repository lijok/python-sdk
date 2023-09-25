import asyncio
import datetime
import logging
import signal
import sys
import threading
import types

from python_sdk.service import _service_config

_HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)
if sys.platform == "win32":
    _HANDLED_SIGNALS += (signal.SIGBREAK,)  # Windows signal 21. Sent by Ctrl+Break.


class Service:
    config: _service_config.Config
    should_exit: bool
    should_force_exit: bool
    started_at: datetime.datetime | None

    def __init__(self, config: _service_config.Config) -> None:
        self.config = config
        self.should_exit = False
        self.should_force_exit = False
        self.started_at = None

    @property
    def elapsed_since_started(self) -> datetime.timedelta:
        if not self.started_at:
            return datetime.timedelta(seconds=0)
        return datetime.datetime.now(tz=datetime.timezone.utc) - self.started_at

    @property
    def _on_tick_callbacks(self) -> asyncio.Future:
        return asyncio.gather(
            self._set_should_exit_flag_if_arrived_at_configured_run_for(),
        )

    def run(self) -> None:
        asyncio.run(self._run())

    def run_in_background(self) -> asyncio.Task[None]:
        return asyncio.create_task(self._run())

    async def _run(self) -> None:
        self._reset()
        logging.debug("Starting service.")
        await self._startup()
        if self.should_exit:
            logging.debug("Service stopped before it got started.")
            return
        await self._main_loop()
        await self._shutdown()

        logging.debug("Service stopped.")

    def _reset(self) -> None:
        """
        Resets the service so it may be reused after a previous run finished.
        """
        self.should_exit = False
        self.should_force_exit = False
        self.started_at = None

    async def _startup(self) -> None:
        self._install_signal_handlers()

    async def _shutdown(self) -> None:
        return

    async def _main_loop(self) -> None:
        self.started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        task = asyncio.create_task(self.config.app.start())
        while not self.should_exit and not task.done():
            await asyncio.sleep(self.config.tick_interval.total_seconds())
            await self._tick()
        if not task.done():
            await self.config.app.stop()

    async def _tick(self) -> None:
        await self._on_tick_callbacks

    def _install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        loop = asyncio.get_event_loop()

        try:
            for sig in _HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self._handle_signal, sig, None)
        except NotImplementedError:
            # Windows
            for sig in _HANDLED_SIGNALS:
                signal.signal(sig, self._handle_signal)

    def _handle_signal(self, sig: int, frame: types.FrameType | None) -> None:
        logging.info(f"Received signal. signal={signal.Signals(sig).name}")
        if self.should_exit and sig == signal.SIGINT:
            self.should_force_exit = True
        else:
            self.should_exit = True

    async def _set_should_exit_flag_if_arrived_at_configured_run_for(self) -> None:
        if self.config.run_for and self.elapsed_since_started >= self.config.run_for:
            self.should_exit = True
