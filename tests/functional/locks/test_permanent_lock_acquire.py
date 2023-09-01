import pytest

from python_sdk import locks


class TestPermanentLockAcquire:
    async def test_can_acquire(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        current_lock = await lock_provider.permanent_lock(key=lock_key).acquire()
        assert current_lock.is_permanent

    async def test_can_acquire_using_context_manager(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        async with lock_provider.permanent_lock(key=lock_key) as lock:
            assert (await lock.current_lock).is_permanent

    async def test_temporary_lock_can_be_made_permanent(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.lock(key=lock_key)
        await lock.acquire()
        current_lock = await lock.make_permanent()
        assert current_lock.is_permanent

    async def test_make_permanent_is_noop(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.lock(key=lock_key)
        await lock.acquire()
        current_lock = await lock.make_permanent()
        assert current_lock.is_permanent
        current_lock = await lock.make_permanent()
        assert current_lock.is_permanent

    async def test_cannot_make_lock_that_is_not_acquired_permanent(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        lock = lock_provider.lock(key=lock_key)
        with pytest.raises(locks.LockNotOwnedByUs):
            await lock.make_permanent()
