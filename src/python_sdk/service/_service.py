import asyncio
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

    def __init__(self, config: _service_config.Config) -> None:
        self.config = config
        self.should_exit = False
        self.should_force_exit = False

    def run(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        await self._reset()
        logging.info(f"Starting service. config={self.config.as_dict}")
        await self._startup()
        if self.should_exit:
            logging.info("Service stopped before it got started.")
            return
        await self._main_loop()
        await self._shutdown()

        logging.info("Service stopped.")

    async def _reset(self) -> None:
        """
        Resets the service so it may be reused after a previous run finished.
        """
        self.should_exit = False
        self.should_force_exit = False

    async def _startup(self) -> None:
        self._install_signal_handlers()

    async def _shutdown(self) -> None:
        return

    async def _main_loop(self) -> None:
        task = asyncio.create_task(self.config.app.start())
        while not self.should_exit and not task.done():
            await asyncio.sleep(0.1)
            await self._tick()
        if not task.done():
            await self.config.app.stop()

    async def _tick(self) -> None:
        return

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
