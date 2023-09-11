import asyncio

from python_sdk import asyncio_atexit


def test_asyncio_atexit_with_sync_callback(event_loop_policy: None) -> None:
    sync_called = False

    def sync_callback() -> None:
        nonlocal sync_called
        sync_called = True
        raise ValueError("Failure shouldn't prevent other callbacks")

    async def test():
        asyncio_atexit.register(sync_callback)

    asyncio.run(test())
    assert sync_called


def test_asyncio_atexit_with_async_callback(event_loop_policy: None) -> None:
    async_called = False

    async def async_callback() -> None:
        nonlocal async_called
        async_called = True

    async def test():
        asyncio_atexit.register(async_callback)

    asyncio.run(test())
    assert async_called


def test_asyncio_atexit_with_both_sync_and_async_callbacks(event_loop_policy: None) -> None:
    sync_called = False
    async_called = False

    def sync_callback() -> None:
        nonlocal sync_called
        sync_called = True
        raise ValueError("Failure shouldn't prevent other callbacks")

    async def async_callback() -> None:
        nonlocal async_called
        async_called = True

    async def test():
        asyncio_atexit.register(sync_callback)
        asyncio_atexit.register(async_callback)

    asyncio.run(test())
    assert sync_called
    assert async_called
