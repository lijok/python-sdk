import datetime

import freezegun

from python_sdk import locks


async def test_current_lock_returns_correct_is_expired_status(lock_provider: locks.LockProvider, lock_key: str) -> None:
    with freezegun.freeze_time() as time:
        lock = lock_provider.lock(lock_key, ttl=datetime.timedelta(seconds=30))
        await lock.acquire()
        await lock._stop_heartbeat()
        assert not (await lock.current_lock).is_expired
        time.tick(datetime.timedelta(seconds=31))
        assert (await lock.current_lock).is_expired
