import asyncio
import datetime

from python_sdk import locks


async def test_held_since_is_set_on_temporary_locks(lock_provider: locks.LockProvider, lock_key: str) -> None:
    assert (await lock_provider.lock(lock_key).acquire()).held_since


async def test_held_since_is_set_on_permanent_locks(lock_provider: locks.LockProvider, lock_key: str) -> None:
    assert (await lock_provider.permanent_lock(lock_key).acquire()).held_since


async def test_held_since_does_not_update(lock_provider: locks.LockProvider, lock_key: str) -> None:
    lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(milliseconds=1))
    original = await lock.acquire()
    await asyncio.sleep(0)  # Give heartbeat a chance to run
    assert (await lock.current_lock).held_since == original.held_since


async def test_held_since_resets_for_new_locks(lock_provider: locks.LockProvider, lock_key: str) -> None:
    lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(milliseconds=1))
    original = await lock.acquire()
    await lock.release()
    new = await lock.acquire()
    assert original.held_since != new.held_since
