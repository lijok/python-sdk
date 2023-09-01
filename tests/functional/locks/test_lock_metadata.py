import uuid

import pytest

from python_sdk import locks


@pytest.mark.parametrize(
    "metadata",
    [
        {"test": "test"},
        {"test": "£@3523T@£T@£"},
        {"test": "👋"},
        {"test": '{"test": 123}'},
        {},
    ],
)
class TestLockMetadata:
    async def test_has_correct_metadata_with_default_metadata(
        self, lock_provider: locks.LockProvider, lock_key: str, metadata: dict[str, str]
    ) -> None:
        lock_provider.default_metadata = metadata
        current_lock = await lock_provider.lock(key=lock_key).acquire()
        assert current_lock.metadata == metadata

    async def test_has_correct_metadata_without_default_metadata(
        self, lock_provider: locks.LockProvider, lock_key: str, metadata: dict[str, str]
    ) -> None:
        current_lock = await lock_provider.lock(lock_key, additional_metadata=metadata).acquire()
        assert current_lock.metadata == metadata

    async def test_additional_metadata_is_merged_into_default_metadata(
        self, lock_provider: locks.LockProvider, lock_key: str, metadata: dict[str, str]
    ) -> None:
        additional_metadata = {str(uuid.uuid4()): "test"}
        lock_provider.default_metadata = metadata
        current_lock = await lock_provider.lock(lock_key, additional_metadata=additional_metadata).acquire()
        assert current_lock.metadata == metadata | additional_metadata


async def test_additional_metadata_takes_precedence_when_keys_clash_with_default_metadata(
    lock_provider: locks.LockProvider,
    lock_key: str,
) -> None:
    lock_provider.default_metadata = {"test": "incorrect"}
    current_lock = await lock_provider.lock(lock_key, additional_metadata={"test": "correct"}).acquire()
    assert current_lock.metadata == {"test": "correct"}
