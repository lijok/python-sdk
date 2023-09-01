import pytest

from python_sdk import locks


@pytest.mark.parametrize(
    "hostname",
    [
        "test",
        "test.local",
        "https://api.acme.com",
        "ftp://api.acme.com",
        "£@3523T@£T@£",
        "👋",
    ],
)
class TestLockHostname:
    async def test_has_correct_hostname(self, lock_provider: locks.LockProvider, lock_key: str, hostname: str) -> None:
        lock_provider.hostname = hostname
        current_lock = await lock_provider.lock(key=lock_key).acquire()
        assert current_lock.hostname == hostname
