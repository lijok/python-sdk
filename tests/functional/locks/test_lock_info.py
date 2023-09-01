import datetime

import freezegun

from python_sdk import locks


async def test_current_lock_returns_empty_lock_info_for_nonexistent_lock(
    lock_provider: locks.LockProvider, lock_key: str
) -> None:
    current_lock = await lock_provider.lock(key="nonexistent").current_lock
    assert current_lock.key == "nonexistent"
    assert current_lock.object is None
    assert current_lock.hostname is None
    assert current_lock.ttl is None
    assert current_lock.metadata is None
    assert current_lock.is_permanent is None
    assert current_lock.acquired_at is None
    assert current_lock.expires_at is None
    assert current_lock.is_owned_by_me is False
    assert current_lock.exists is False
    assert current_lock.owner_guid is None
    assert current_lock.expires_in is None
    assert current_lock.is_expired is False
    assert current_lock.held_since is None


@freezegun.freeze_time()
async def test_temporary_lock_info_returned_on_acquire_is_identical_to_one_returned_on_request(
    lock_provider: locks.LockProvider,
    lock_key: str,
) -> None:
    lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(seconds=30))
    acquired_lock_info = await lock.acquire()
    current_lock_info = await lock.current_lock
    for attribute in locks.LockInfo.__annotations__.keys():
        assert getattr(acquired_lock_info, attribute) == getattr(current_lock_info, attribute)


@freezegun.freeze_time()
async def test_permanent_lock_info_returned_on_acquire_is_identical_to_one_returned_on_request(
    lock_provider: locks.LockProvider,
    lock_key: str,
) -> None:
    lock = lock_provider.permanent_lock(key=lock_key)
    acquired_lock_info = await lock.acquire()
    current_lock_info = await lock.current_lock
    for attribute in locks.LockInfo.__annotations__.keys():
        assert getattr(acquired_lock_info, attribute) == getattr(current_lock_info, attribute)
