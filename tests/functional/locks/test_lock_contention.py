import asyncio
import datetime
import os

import pytest

from python_sdk import locks


# @pytest.mark.skipif(condition="CI" not in os.environ, reason="Too slow.")
class TestLockContention:
    async def test_cannot_acquire_taken_lock(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        await lock_provider.lock(key=lock_key).acquire()
        with pytest.raises(locks.LockAcquisitionError):
            await lock_provider.lock(key=lock_key).acquire()

    async def test_cannot_acquire_taken_lock_with_same_owner(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        async with lock_provider.lock(key=lock_key) as lock:
            with pytest.raises(locks.LockAcquisitionError):
                await lock.acquire()

    async def test_cannot_acquire_taken_permanent_lock(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        await lock_provider.permanent_lock(key=lock_key).acquire()
        with pytest.raises(locks.LockAcquisitionError):
            await lock_provider.lock(key=lock_key).acquire()

    async def test_cannot_acquire_taken_permanent_lock_with_same_owner(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        async with lock_provider.lock(key=lock_key) as lock:
            with pytest.raises(locks.LockAcquisitionError):
                await lock.acquire()

    async def test_can_acquire_expired_lock(self, lock_provider: locks.LockProvider, lock_key: str) -> None:
        lock1 = lock_provider.lock(lock_key, ttl=datetime.timedelta(milliseconds=1))
        await lock1.acquire()
        await lock1._stop_heartbeat()
        await lock_provider.lock(key=lock_key).acquire()

    async def test_concurrent_requests_for_same_lock_result_in_one_lock(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        concurrent_lock_request_results = await asyncio.gather(
            *[lock_provider.lock(key=lock_key).acquire() for _ in range(100)], return_exceptions=True
        )
        assert len([i for i in concurrent_lock_request_results if isinstance(i, locks.LockInfo)]) == 1
        assert len([i for i in concurrent_lock_request_results if isinstance(i, locks.LockAcquisitionError)]) == 99

    async def test_concurrent_requests_for_same_expired_lock_result_in_one_lock(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(milliseconds=1))
        await lock.acquire()
        await lock._stop_heartbeat()
        concurrent_lock_request_results = await asyncio.gather(
            *[lock_provider.lock(key=lock_key).acquire() for _ in range(100)], return_exceptions=True
        )
        assert len([i for i in concurrent_lock_request_results if isinstance(i, locks.LockInfo)]) == 1
        assert len([i for i in concurrent_lock_request_results if isinstance(i, locks.LockAcquisitionError)]) == 99
