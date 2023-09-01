import datetime

import pytest

from python_sdk import locks


class TestTemporaryLockAcquire:
    async def test_can_acquire(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        assert await lock_provider.lock(key=lock_key).acquire()

    async def test_can_acquire_using_context_manager(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        async with lock_provider.lock(key=lock_key) as lock:
            pass

    async def test_cannot_acquire_with_ttl_of_zero(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        with pytest.raises(ValueError):
            await lock_provider.lock(key=lock_key, ttl=datetime.timedelta(seconds=0)).acquire()
