import typing

import pytest

from python_sdk import locks


# TODO: Restrict object types
@pytest.mark.parametrize(
    "object",
    [
        "test",
        123,
        {"test": "Test"},
        '{"test": "Test"}',
        # b"test",
        None,
    ],
)
class TestLockObject:
    async def test_has_correct_object(
        self, lock_provider: locks.LockProvider, lock_key: str, object: typing.Any
    ) -> None:
        current_lock = await lock_provider.lock(lock_key, object=object).acquire()
        assert current_lock.object == object
