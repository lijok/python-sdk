import datetime
import random

import pytest

from python_sdk import locks


@pytest.mark.parametrize(
    "ttl",
    [
        datetime.timedelta(milliseconds=0.001),
        datetime.timedelta(milliseconds=100),
        datetime.timedelta(seconds=60),
        datetime.timedelta(days=7),
        datetime.timedelta(days=365 * 100),
    ],
)
class TestLockTTL:
    async def test_has_correct_ttl_with_default_ttl(
        self, lock_provider: locks.LockProvider, lock_key: str, ttl: datetime.timedelta
    ) -> None:
        lock_provider.default_ttl = ttl
        current_lock = await lock_provider.lock(key=lock_key).acquire()
        assert current_lock.ttl == ttl

    async def test_can_override_default_ttl_when_acquiring_temporary_lock(
        self, lock_provider: locks.LockProvider, lock_key: str, ttl: datetime.timedelta
    ) -> None:
        lock_provider.default_ttl = datetime.timedelta(seconds=random.randint(0, 9999999))
        current_lock = await lock_provider.lock(lock_key, ttl=ttl).acquire()
        assert current_lock.ttl == ttl

    async def test_permanent_locks_do_not_have_ttl_when_default_ttl_is_set(
        self, lock_provider: locks.LockProvider, lock_key: str, ttl: datetime.timedelta
    ) -> None:
        lock_provider.default_ttl = ttl
        current_lock = await lock_provider.permanent_lock(key=lock_key).acquire()
        assert current_lock.ttl is None

    async def test_locks_made_permanent_have_their_ttl_removed_when_default_ttl_is_set(
        self, lock_provider: locks.LockProvider, lock_key: str, ttl: datetime.timedelta
    ) -> None:
        lock_provider.default_ttl = ttl
        lock = lock_provider.lock(key=lock_key)
        await lock.acquire()
        current_lock = await lock.make_permanent()
        assert current_lock.ttl is None


async def test_permanent_locks_do_not_have_ttl(lock_provider: locks.LockProvider, lock_key: str) -> None:
    current_lock = await lock_provider.permanent_lock(key=lock_key).acquire()
    assert current_lock.ttl is None
