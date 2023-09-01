import pytest

from python_sdk import locks


@pytest.mark.parametrize(
    "key",
    [
        "test",
        "test.local",
        "https://api.acme.com",
        "ftp://api.acme.com",
        "£@3523T@£T@£",
        "👋",
        "/locks/acme/my-lock.lock",
        "locks/acme/my-lock.lock",
    ],
)
class TestLockKey:
    async def test_lock_key_is_correct(self, lock_provider: locks.LockProvider, key: str) -> None:
        current_lock = await lock_provider.lock(key=key).acquire()
        assert current_lock.key == key
