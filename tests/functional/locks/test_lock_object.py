import typing

import pytest

from python_sdk import locks


@pytest.mark.parametrize(
    "object",
    [
        "test",
        {"test": "Test"},
        {"test": {"Test": "test"}},
        {"test": ["test"]},
        '{"test": "Test"}',
        None,
    ],
)
class TestLockObject:
    async def test_has_correct_object(
        self, lock_provider: locks.LockProvider, lock_key: str, object: typing.Any
    ) -> None:
        current_lock = await lock_provider.lock(lock_key, object=object).acquire()
        assert current_lock.object == object
