import asyncio
import datetime
import os
import time

import pytest

from python_sdk import locks


# @pytest.mark.skipif(condition="CI" not in os.environ, reason="Too slow.")
class TestTemporaryLockRefresh:
    async def test_lock_is_automatically_refreshed(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(milliseconds=500))
        new_lock = await lock.acquire()
        await asyncio.sleep(0.1)
        current_lock = await lock.current_lock
        assert new_lock.expires_at
        assert current_lock.expires_at
        assert current_lock.expires_at > new_lock.expires_at

    async def test_lock_is_not_refreshed_if_it_was_made_permanent(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(milliseconds=500))
        await lock.acquire()
        await lock.make_permanent()
        await asyncio.sleep(0.5)  # Give heartbeat a chance to run
        assert (await lock.current_lock).expires_at is None

    async def test_lock_is_refreshed_if_it_timed_out(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(milliseconds=500))
        await lock.acquire()
        time.sleep(0.1)  # Block to cause a timeout
        await asyncio.sleep(0.1)  # Give heartbeat a chance to run
        assert not (await lock.current_lock).is_expired

    async def test_lock_is_not_refreshed_if_it_got_removed_via_force_unlock(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(milliseconds=100))
        await lock.acquire()
        await lock_provider.lock(lock_key).force_release()
        await asyncio.sleep(0)  # Give heartbeat a chance ot run
        assert not (await lock.current_lock).exists

    async def test_cannot_refresh_lock_that_hasnt_been_acquired(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        lock = lock_provider.lock(lock_key)
        with pytest.raises(locks.LockNotOwnedByUs):
            await lock.refresh()

    async def test_cannot_refresh_lock_that_doesnt_belong_to_us(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        await lock_provider.lock(lock_key).acquire()
        lock = lock_provider.lock(lock_key)
        with pytest.raises(locks.LockNotOwnedByUs):
            await lock.refresh()

    async def test_cannot_refresh_lock_that_was_stolen(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock = lock_provider.lock(lock_key)
        await lock.acquire()
        await lock_provider.lock(lock_key).force_release()
        await lock_provider.lock(lock_key).acquire()
        with pytest.raises(locks.LockNotOwnedByUs):
            await lock.refresh()
