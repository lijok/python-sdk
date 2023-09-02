import pytest

from python_sdk import locks


class TestPermanentLockRelease:
    async def test_cannot_release(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.permanent_lock(key=lock_key)
        await lock.acquire()
        with pytest.raises(locks.LockIsPermanent):
            await lock.release()

    async def test_is_not_released_on_context_manager_exit(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        async with lock_provider.permanent_lock(key=lock_key) as lock:
            pass
        assert (await lock.current_lock).exists
        assert (await lock.current_lock).is_owned_by_me

    async def test_is_not_released_on_context_manager_exit_when_error_occurs(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        with pytest.raises(ModuleNotFoundError):
            async with lock_provider.permanent_lock(key=lock_key) as lock:
                raise ModuleNotFoundError()
        assert (await lock.current_lock).exists
        assert (await lock.current_lock).is_owned_by_me

    async def test_can_force_release(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.permanent_lock(key=lock_key)
        await lock.acquire()
        await lock.force_release()

    async def test_can_force_release_from_context_manager(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        async with lock_provider.permanent_lock(key=lock_key) as lock:
            await lock.force_release()

    async def test_can_force_release_without_being_the_owner(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        await lock_provider.permanent_lock(key=lock_key).acquire()
        await lock_provider.lock(key=lock_key).force_release()

    async def test_force_release_is_idempotent(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        await lock_provider.permanent_lock(key=lock_key).acquire()
        await lock_provider.lock(key=lock_key).force_release()
        await lock_provider.lock(key=lock_key).force_release()


async def test_permanent_lock_does_not_expire(lock_provider: locks.LockProvider, lock_key: str) -> None:
    lock = lock_provider.permanent_lock(key=lock_key)
    current_lock = await lock.acquire()
    assert current_lock.expires_at is None
    assert current_lock.expires_in is None
    assert current_lock.is_expired is False
    assert current_lock.ttl is None
