import asyncio

from python_sdk import asyncio_atexit


class TestRegisterSyncCallable:
    def test_can_unregister(self, event_loop_policy: None) -> None:
        called = False

        def callback() -> None:
            nonlocal called
            called = True

        async def test():
            asyncio_atexit.register(callback)
            asyncio_atexit.unregister(callback)

        asyncio.run(test())
        assert not called

    def test_all_instances_are_unregistered(self, event_loop_policy: None) -> None:
        called = False

        def callback() -> None:
            nonlocal called
            called = True

        async def test():
            asyncio_atexit.register(callback)
            asyncio_atexit.register(callback)
            asyncio_atexit.unregister(callback)

        asyncio.run(test())
        assert not called
