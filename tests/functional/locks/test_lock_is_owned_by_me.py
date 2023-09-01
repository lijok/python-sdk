from python_sdk import locks


async def test_nonexistant_lock_is_not_owned_by_me(lock_provider: locks.LockProvider, lock_key: str) -> None:
    assert not (await lock_provider.lock(key="nonexistent").current_lock).is_owned_by_me


async def test_temporary_lock_acquired_by_me_is_owned_by_me(lock_provider: locks.LockProvider, lock_key: str) -> None:
    lock = lock_provider.lock(key=lock_key)
    assert (await lock.acquire()).is_owned_by_me
    assert (await lock.current_lock).is_owned_by_me


async def test_permanent_lock_acquired_by_me_is_owned_by_me(lock_provider: locks.LockProvider, lock_key: str) -> None:
    lock = lock_provider.permanent_lock(key=lock_key)
    assert (await lock.acquire()).is_owned_by_me
    assert (await lock.current_lock).is_owned_by_me


async def test_temporary_lock_not_acquired_by_me_is_not_owned_by_me(
    lock_provider: locks.LockProvider, lock_key: str
) -> None:
    await lock_provider.lock(key=lock_key).acquire()
    assert not (await lock_provider.lock(key=lock_key).current_lock).is_owned_by_me


async def test_permanent_lock_not_acquired_by_me_is_not_owned_by_me(
    lock_provider: locks.LockProvider, lock_key: str
) -> None:
    await lock_provider.permanent_lock(key=lock_key).acquire()
    assert not (await lock_provider.lock(key=lock_key).current_lock).is_owned_by_me
