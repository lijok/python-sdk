import asyncio
import datetime
import typing

from python_sdk import locks


class TestPermanentLockAcquireRetries:
    async def await_with_delay(self, awaitable: typing.Awaitable, delay: datetime.timedelta) -> None:
        await asyncio.sleep(delay.total_seconds())
        await awaitable

    async def test_retry_aborts_early_if_current_lock_is_permanent(
        self, lock_provider: locks.LockProvider, lock_key: str
    ) -> None:
        lock = lock_provider.permanent_lock(key=lock_key)
        await lock.acquire()
        maybe_new_lock, _ = await asyncio.gather(
            lock_provider.lock(
                key=lock_key,
                retry_times=10,
                retry_delay=datetime.timedelta(milliseconds=100),
            ).acquire(),
            self.await_with_delay(
                awaitable=lock.force_release(),
                delay=datetime.timedelta(milliseconds=200),
            ),
            return_exceptions=True,
        )
        assert isinstance(maybe_new_lock, locks.LockTaken)
