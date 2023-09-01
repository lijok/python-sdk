from python_sdk import locks


async def test_lock_owner_guid_is_different_for_each_lock_instance(
    lock_provider: locks.LockProvider, lock_key: str
) -> None:
    lock_1 = await lock_provider.lock(key=lock_key).acquire()
    lock_2 = await lock_provider.lock(key=f"{lock_key}-2").acquire()
    assert lock_1.owner_guid != lock_2.owner_guid
