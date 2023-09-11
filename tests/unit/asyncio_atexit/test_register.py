import asyncio

from python_sdk import asyncio_atexit


class TestRegisterSyncCallable:
    def test_can_register_via_function_call(self, event_loop_policy: None) -> None:
        called = False

        def callback() -> None:
            nonlocal called
            called = True

        async def test():
            asyncio_atexit.register(callback)

        asyncio.run(test())
        assert called

    def test_can_register_via_decorator(self, event_loop_policy: None) -> None:
        called = False

        async def test():
            @asyncio_atexit.register
            def callback() -> None:
                nonlocal called
                called = True

        asyncio.run(test())
        assert called

    def test_can_register_with_args(self, event_loop_policy: None) -> None:
        result = None
        desired_result = "True"

        def callback(desired_result: str) -> None:
            nonlocal result
            result = desired_result

        async def test():
            asyncio_atexit.register(callback, desired_result)

        asyncio.run(test())
        assert result == desired_result
