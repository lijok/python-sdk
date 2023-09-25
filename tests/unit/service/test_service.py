import asyncio
import datetime

from python_sdk import service


class App:
    should_stop: bool
    counter: int

    def __init__(self) -> None:
        self.should_stop = False
        self.counter = 0

    async def start(self) -> None:
        while not self.should_stop:
            self.counter += 1
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        self.should_stop = True


async def test_service_can_be_run() -> None:
    app = App()
    SERVICE = service.Service(config=service.Config(app=app))
    task = SERVICE.run_in_background()
    await asyncio.sleep(0.1)
    assert app.counter > 0
    await app.stop()
    await asyncio.sleep(0.1)
    assert task.done()


async def test_service_can_be_run_for_specified_amount_of_time() -> None:
    app = App()
    SERVICE = service.Service(config=service.Config(app=app, run_for=datetime.timedelta(seconds=0.5)))
    task = SERVICE.run_in_background()
    await asyncio.sleep(1)
    assert app.counter > 0
    assert app.counter < 7
    assert app.should_stop
    assert SERVICE.should_exit
    assert task.done()
