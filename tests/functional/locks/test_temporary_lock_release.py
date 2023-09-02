import asyncio
import datetime
import os

import pytest

from python_sdk import locks


class TestTemporaryLockRelease:
    async def test_can_release(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.lock(key=lock_key)
        await lock.acquire()
        await lock.release()
        assert not (await lock.current_lock).exists

    async def test_cannot_release_without_being_the_owner(
        self,
        lock_provider: locks.LockProvider,
        lock_key: str,
    ) -> None:
        await lock_provider.lock(key=lock_key).acquire()
        assert (await lock_provider.lock(key=lock_key).current_lock).exists
        with pytest.raises(locks.LockNotOwnedByUs):
            await lock_provider.lock(key=lock_key).release()

    async def test_context_manager_releases_on_context_exit(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        async with lock_provider.lock(key=lock_key) as lock:
            pass
        assert not (await lock.current_lock).exists
        assert not (await lock.current_lock).is_owned_by_me

    async def test_context_manager_releases_on_context_exit_when_error_occurs(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        with pytest.raises(ModuleNotFoundError):
            async with lock_provider.lock(key=lock_key) as lock:
                raise ModuleNotFoundError()
        assert not (await lock.current_lock).exists
        assert not (await lock.current_lock).is_owned_by_me

    async def test_can_force_release(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.lock(key=lock_key)
        await lock.acquire()
        await lock.force_release()

    async def test_can_force_release_from_context_manager(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        async with lock_provider.lock(key=lock_key) as lock:
            await lock.force_release()

    async def test_can_force_release_without_being_the_owner(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        await lock_provider.lock(key=lock_key).acquire()
        await lock_provider.lock(key=lock_key).force_release()

    @pytest.mark.skipif(condition="CI" not in os.environ, reason="CI only - too slow.")
    async def test_stolen_locks_are_not_released_by_original_owner(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        await lock_provider.lock(key=lock_key, ttl=datetime.timedelta(seconds=5)).acquire()
        thief_lock = lock_provider.lock(key=lock_key, ttl=datetime.timedelta(seconds=5))
        await thief_lock.force_release()
        stolen_lock = await thief_lock.acquire()
        await asyncio.sleep(2.5)  # Give heartbeat a chance to run
        assert (await thief_lock.current_lock).owner_guid == stolen_lock.owner_guid

    async def test_force_release_is_idempotent(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        await lock_provider.lock(key=lock_key).acquire()
        await lock_provider.lock(key=lock_key).force_release()
        await lock_provider.lock(key=lock_key).force_release()
