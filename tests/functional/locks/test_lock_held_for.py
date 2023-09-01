import asyncio

from python_sdk import locks


async def test_held_for_is_set_on_temporary_locks(lock_provider: locks.LockProvider, lock_key: str) -> None:
    assert (await lock_provider.lock(lock_key).acquire()).held_for


async def test_held_for_is_set_on_permanent_locks(lock_provider: locks.LockProvider, lock_key: str) -> None:
    assert (await lock_provider.permanent_lock(lock_key).acquire()).held_for


async def test_held_for_ticks_upwards(lock_provider: locks.LockProvider, lock_key: str) -> None:
    lock_info = await lock_provider.lock(lock_key).acquire()
    now = lock_info.held_for
    await asyncio.sleep(0)
    later = lock_info.held_for
    assert now
    assert later
    assert now < later
