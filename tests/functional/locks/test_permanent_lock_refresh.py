import pytest

from python_sdk import locks


class TestPermanentLockRefresh:
    async def test_cannot_refresh_permanent_lock(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.permanent_lock(lock_key)
        with pytest.raises(locks.LockIsPermanent):
            await lock.refresh()

    async def test_cannot_refresh_lock_that_hasnt_been_acquired(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        lock = lock_provider.permanent_lock(lock_key)
        with pytest.raises(locks.LockIsPermanent):
            await lock.refresh()

    async def test_cannot_refresh_lock_that_was_turned_permanent(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        lock = lock_provider.permanent_lock(lock_key)
        await lock.acquire()
        await lock.make_permanent()
        with pytest.raises(locks.LockIsPermanent):
            await lock.refresh()
