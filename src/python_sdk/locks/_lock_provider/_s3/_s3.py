from __future__ import annotations

import asyncio
import datetime
import json
import logging
import socket
import types
import typing
import uuid

import botocore.exceptions

from python_sdk.locks._lock_provider import _exceptions
from python_sdk.locks._lock_provider import _protocol

if typing.TYPE_CHECKING:
    import mypy_boto3_s3


class S3LockProvider:
    """
    Implements a lock provider using S3.

    WARNING:
        Due to S3 not supporting transactions, safe locks are not possible to implement in S3.
        DO NOT use this lock provider if you need guaranteed lock safety.
        To reduce lock contention this provider makes additional API calls to S3 for each lock operation
        and is therefore less performant than other lock providers.
        This lock provider should only be used in applications where occasional lock theft and reduced performance
        is acceptable.
    """

    hostname: str
    default_ttl: datetime.timedelta
    default_metadata: dict[str, str]
    default_retry_times: int
    default_retry_delay: datetime.timedelta
    _s3_client: mypy_boto3_s3.S3Client
    bucket_name: str
    lock_key_prefix: str

    def __init__(
        self,
        hostname: str | None,
        default_ttl: datetime.timedelta,
        default_metadata: dict[str, str],
        default_retry_times: int,
        default_retry_delay: datetime.timedelta,
        s3_client: mypy_boto3_s3.S3Client,
        bucket_name: str,
        lock_key_prefix: str,
    ) -> None:
        self.hostname = hostname or socket.gethostname()
        self.default_ttl = default_ttl
        self.default_metadata = default_metadata or {}
        self.default_retry_times = default_retry_times
        self.default_retry_delay = default_retry_delay
        self._s3_client = s3_client
        self.bucket_name = bucket_name
        self.lock_key_prefix = lock_key_prefix

    def lock(
        self,
        key: str,
        object: typing.Any | None = None,
        ttl: datetime.timedelta | None = None,
        additional_metadata: dict[str, str] | None = None,
        retry_times: int | None = None,
        retry_delay: datetime.timedelta | None = None,
    ) -> S3Lock:
        key = self.lock_key_prefix + key
        ttl = ttl if ttl is not None else self.default_ttl
        metadata = self.default_metadata | (additional_metadata or {})

        return S3Lock(
            key=key,
            object=object,
            hostname=self.hostname,
            ttl=ttl,
            metadata=metadata,
            is_permanent=False,
            retry_times=retry_times or self.default_retry_times,
            retry_delay=retry_delay or self.default_retry_delay,
            s3_client=self._s3_client,
            bucket_name=self.bucket_name,
        )

    def permanent_lock(
        self,
        key: str,
        object: typing.Any | None = None,
        additional_metadata: dict[str, str] | None = None,
        retry_times: int | None = None,
        retry_delay: datetime.timedelta | None = None,
    ) -> S3Lock:
        key = self.lock_key_prefix + key
        metadata = self.default_metadata | (additional_metadata or {})

        return S3Lock(
            key=key,
            object=object,
            hostname=self.hostname,
            ttl=None,
            metadata=metadata,
            is_permanent=True,
            retry_times=retry_times or self.default_retry_times,
            retry_delay=retry_delay or self.default_retry_delay,
            s3_client=self._s3_client,
            bucket_name=self.bucket_name,
        )


class S3Lock:
    key: str
    object: typing.Any | None
    hostname: str
    ttl: datetime.timedelta | None
    metadata: dict[str, str]
    is_permanent: bool
    retry_times: int
    retry_delay: datetime.timedelta
    _s3_client: mypy_boto3_s3.S3Client
    bucket_name: str
    _owner_guid: str
    _heartbeat_task: asyncio.Task[None] | None
    _held_since: datetime.datetime | None

    def __init__(
        self,
        key: str,
        object: typing.Any | None,
        hostname: str,
        ttl: datetime.timedelta | None,
        metadata: dict[str, str],
        is_permanent: bool,
        retry_times: int,
        retry_delay: datetime.timedelta,
        s3_client: mypy_boto3_s3.S3Client,
        bucket_name: str,
    ):
        if ttl == datetime.timedelta(seconds=0) and not is_permanent:
            raise ValueError("TTL must be higher than 0 seconds for temporary locks.")

        self.key = key
        self.object = object
        self.hostname = hostname
        self.ttl = ttl
        self.metadata = metadata
        self.is_permanent = is_permanent
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self._s3_client = s3_client
        self.bucket_name = bucket_name
        self._owner_guid = str(uuid.uuid4())
        self._heartbeat_task = None
        self._held_since = None

    @property
    async def current_lock(self) -> _protocol.LockInfo:
        try:
            response = await asyncio.to_thread(
                self._s3_client.get_object,
                Bucket=self.bucket_name,
                Key=self.key,
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return _protocol.LockInfo(
                    key=self.key,
                    object=None,
                    hostname=None,
                    ttl=None,
                    metadata=None,
                    is_permanent=None,
                    acquired_at=None,
                    expires_at=None,
                    is_owned_by_me=False,
                    exists=False,
                    owner_guid=None,
                    held_since=None,
                )

            raise

        data = json.loads(response["Body"].read().decode("utf-8"))
        return _protocol.LockInfo(
            key=data["key"],
            object=data["object"],
            hostname=data["hostname"],
            ttl=datetime.timedelta(seconds=data["ttl"]) if data["ttl"] else None,
            metadata=data["metadata"],
            is_permanent=data["is_permanent"],
            acquired_at=datetime.datetime.fromisoformat(data["acquired_at"]) if data["acquired_at"] else None,
            expires_at=datetime.datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            is_owned_by_me=data["owner_guid"] == self._owner_guid,
            exists=True,
            owner_guid=data["owner_guid"],
            held_since=datetime.datetime.fromisoformat(data["held_since"]),
        )

    async def __aenter__(self) -> S3Lock:
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        await self._stop_heartbeat()
        try:
            await self.release()
        except _exceptions.LockNotOwnedByUs:
            logging.warning(
                "Could not release the lock as it is no longer owned by us. "
                "The lock may have been stolen by a malfunctioning 3rd party or we may have lost it by not refreshing "
                "due to a blocked process. "
                "If this is happening often, consider increasing the TTL of your locks. "
                f"key={self.key} "
                f"hostname={self.hostname} "
                f"ttl={self.ttl} "
                f"held_since={self._held_since}"
            )
        except _exceptions.LockIsPermanent:
            # Lock was made permanent while in the context manager, this is fine.
            pass
        except Exception:
            logging.exception(
                "Encountered unhandled exception while attempting to release the lock during context manager exit. "
                f"key={self.key} "
                f"hostname={self.hostname} "
                f"ttl={self.ttl} "
                f"held_since={self._held_since}"
            )

    async def acquire(self) -> _protocol.LockInfo:
        tries_left = self.retry_times + 1

        while tries_left:
            tries_left -= 1

            logging.debug(
                "Trying to acquire lock. "
                f"retry_times={self.retry_times} "
                f"retry_delay={self.retry_delay} "
                f"tries_left={tries_left}"
            )

            try:
                return await self._acquire()
            except _exceptions.LockTaken as e:
                if e.current_lock.is_permanent:
                    logging.debug(
                        "Failed to acquire lock. Current lock is permanent. "
                        f"retry_times={self.retry_times} "
                        f"retry_delay={self.retry_delay} "
                        f"tries_left={tries_left}"
                    )
                    raise
                elif tries_left:
                    await asyncio.sleep(self.retry_delay.total_seconds())
                else:
                    logging.debug(
                        "Failed to acquire lock. Out of tries. "
                        f"retry_times={self.retry_times} "
                        f"retry_delay={self.retry_delay} "
                        f"tries_left={tries_left}"
                    )
                    raise

    async def _acquire(self) -> _protocol.LockInfo:
        existing_lock = await self.current_lock
        if existing_lock.exists and (existing_lock.is_permanent or not existing_lock.is_expired):
            logging.debug(f"Failed to acquire lock. Lock taken. key={self.key}")
            raise _exceptions.LockTaken(current_lock=existing_lock)

        self._held_since = datetime.datetime.now(tz=datetime.timezone.utc)
        new_lock = self._new_lock_info

        logging.debug(
            "Acquiring lock. "
            f"key={new_lock.key} "
            f"hostname={new_lock.hostname} "
            f"ttl={new_lock.ttl} "
            f"metadata={new_lock.metadata} "
            f"is_permanent={new_lock.is_permanent} "
            f"expires_at={new_lock.expires_at} "
            f"owner_guid={new_lock.owner_guid} "
            f"held_since={new_lock.held_since}"
        )

        await asyncio.to_thread(
            self._s3_client.put_object,
            Bucket=self.bucket_name,
            Key=self.key,
            Body=self._lock_info_to_s3_object(lock_info=new_lock),
            ContentType="application/json",
        )

        current_lock = await self.current_lock
        if not current_lock.is_owned_by_me:
            # Lock got overwritten right after we wrote it.
            # As we don't have transactions in S3, this can happen when contention occurs.
            logging.debug(f"Failed to acquire lock. Lock taken. key={self.key}")
            raise _exceptions.LockTaken(current_lock=current_lock)

        logging.debug(
            "Lock acquired. "
            f"key={new_lock.key} "
            f"hostname={new_lock.hostname} "
            f"ttl={new_lock.ttl} "
            f"metadata={new_lock.metadata} "
            f"is_permanent={new_lock.is_permanent} "
            f"acquired_at={new_lock.acquired_at} "
            f"expires_at={new_lock.expires_at} "
            f"owner_guid={new_lock.owner_guid} "
            f"held_since={new_lock.held_since}"
        )

        if not self.is_permanent:
            await self._start_heartbeat()

        return current_lock

    async def refresh(self) -> _protocol.LockInfo:
        current_lock = await self.current_lock

        if self.is_permanent:
            raise _exceptions.LockIsPermanent(current_lock=current_lock)

        if not current_lock.is_owned_by_me:
            raise _exceptions.LockNotOwnedByUs(current_lock=current_lock)

        new_lock = self._new_lock_info

        logging.debug(
            "Refreshing lock. "
            f"key={new_lock.key} "
            f"hostname={new_lock.hostname} "
            f"ttl={new_lock.ttl} "
            f"metadata={new_lock.metadata} "
            f"is_permanent={new_lock.is_permanent} "
            f"acquired_at={new_lock.acquired_at} "
            f"expires_at={new_lock.expires_at} "
            f"owner_guid={new_lock.owner_guid} "
            f"held_since={new_lock.held_since}"
        )

        await asyncio.to_thread(
            self._s3_client.put_object,
            Bucket=self.bucket_name,
            Key=self.key,
            Body=self._lock_info_to_s3_object(lock_info=new_lock),
            ContentType="application/json",
        )

        current_lock = await self.current_lock
        if not current_lock.is_owned_by_me:
            # Lock got overwritten right after we wrote it.
            # As we don't have transactions in S3, this can happen when contention occurs.
            # However, unlike when acquiring a new lock, this should only happen when refreshing
            # a lock which is on the cusp of expiring.
            # Therefore, if this does occur, we want to warn the user.

            logging.warning(
                "Lock was stolen. "
                f"key={new_lock.key} "
                f"hostname={new_lock.hostname} "
                f"ttl={new_lock.ttl} "
                f"metadata={new_lock.metadata} "
                f"is_permanent={new_lock.is_permanent} ",
                f"held_since={new_lock.held_since} ",
                f"stolen_by_hostname={current_lock.hostname} ",
                f"stolen_by_metadata={current_lock.metadata} ",
                f"stolen_by_owner_guid={current_lock.owner_guid}",
            )

            raise _exceptions.LockNotOwnedByUs(current_lock=current_lock)

        logging.debug(
            "Lock refreshed. "
            f"key={current_lock.key} "
            f"hostname={current_lock.hostname} "
            f"ttl={current_lock.ttl} "
            f"metadata={current_lock.metadata} "
            f"is_permanent={current_lock.is_permanent} "
            f"acquired_at={current_lock.acquired_at} "
            f"expires_at={current_lock.expires_at} "
            f"owner_guid={current_lock.owner_guid} "
            f"held_since={current_lock.held_since}"
        )

        return current_lock

    async def make_permanent(self) -> _protocol.LockInfo:
        current_lock = await self.current_lock

        if not current_lock.is_owned_by_me:
            raise _exceptions.LockNotOwnedByUs(current_lock=current_lock)

        await self._stop_heartbeat()
        self.is_permanent = True
        self.ttl = None

        new_lock = self._new_lock_info

        logging.debug(
            "Making lock permanent. "
            f"key={new_lock.key} "
            f"hostname={new_lock.hostname} "
            f"ttl={new_lock.ttl} "
            f"metadata={new_lock.metadata} "
            f"is_permanent={new_lock.is_permanent} "
            f"acquired_at={new_lock.acquired_at} "
            f"expires_at={new_lock.expires_at} "
            f"owner_guid={new_lock.owner_guid} "
            f"held_since={new_lock.held_since}"
        )

        await asyncio.to_thread(
            self._s3_client.put_object,
            Bucket=self.bucket_name,
            Key=self.key,
            Body=self._lock_info_to_s3_object(lock_info=new_lock),
            ContentType="application/json",
        )

        current_lock = await self.current_lock
        if not current_lock.is_owned_by_me:
            # Lock got overwritten right after we wrote it.
            # As we don't have transactions in S3, this can happen when contention occurs.
            # However, unlike when acquiring a new lock, this should only happen when changing
            # a lock which is on the cusp of expiring.
            # Therefore, if this does occur, we want to warn the user.

            logging.warning(
                "Lock was stolen. "
                f"key={new_lock.key} "
                f"hostname={new_lock.hostname} "
                f"ttl={new_lock.ttl} "
                f"metadata={new_lock.metadata} "
                f"is_permanent={new_lock.is_permanent} ",
                f"held_since={new_lock.held_since} ",
                f"stolen_by_hostname={current_lock.hostname} ",
                f"stolen_by_metadata={current_lock.metadata} ",
                f"stolen_by_owner_guid={current_lock.owner_guid}",
            )

            raise _exceptions.LockNotOwnedByUs(current_lock=current_lock)

        logging.debug(
            "Lock made permanent. "
            f"key={new_lock.key} "
            f"hostname={new_lock.hostname} "
            f"ttl={new_lock.ttl} "
            f"metadata={new_lock.metadata} "
            f"is_permanent={new_lock.is_permanent} "
            f"acquired_at={new_lock.acquired_at} "
            f"expires_at={new_lock.expires_at} "
            f"owner_guid={new_lock.owner_guid} "
            f"held_since={new_lock.held_since}"
        )

        return new_lock

    async def release(self) -> None:
        await self._stop_heartbeat()

        current_lock = await self.current_lock
        if not current_lock.exists:
            return

        if not current_lock.is_owned_by_me:
            raise _exceptions.LockNotOwnedByUs(current_lock=current_lock)

        if current_lock.is_permanent:
            raise _exceptions.LockIsPermanent(current_lock=current_lock)

        logging.debug(f"Releasing lock. key={self.key}")

        try:
            await asyncio.to_thread(
                self._s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=self.key,
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logging.warning(f"Lock was released by another process. key={self.key}")
                return

            raise

        logging.debug(f"Lock released. key={self.key}")
        return

    async def force_release(self) -> None:
        await self._stop_heartbeat()
        logging.debug(f"Force releasing lock. key={self.key}")

        try:
            await asyncio.to_thread(
                self._s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=self.key,
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logging.warning(f"Lock was released by another process. key={self.key}")
                return

            raise

        logging.debug(f"Lock released forcefully. key={self.key}")
        return

    @property
    def _new_lock_info(self) -> _protocol.LockInfo:
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        return _protocol.LockInfo(
            key=self.key,
            object=self.object,
            hostname=self.hostname,
            ttl=self.ttl,
            metadata=self.metadata,
            is_permanent=self.is_permanent,
            acquired_at=now,
            expires_at=None if self.is_permanent else now + self.ttl,
            is_owned_by_me=True,
            exists=True,
            owner_guid=self._owner_guid,
            held_since=self._held_since,
        )

    def _lock_info_to_s3_object(self, lock_info: _protocol.LockInfo) -> str:
        return json.dumps(
            {
                "key": lock_info.key,
                "object": lock_info.object,
                "hostname": lock_info.hostname,
                "ttl": lock_info.ttl.total_seconds() if lock_info.ttl else None,
                "metadata": lock_info.metadata,
                "is_permanent": lock_info.is_permanent,
                "acquired_at": lock_info.acquired_at.isoformat(),
                "expires_at": lock_info.expires_at.isoformat() if lock_info.expires_at else None,
                "owner_guid": lock_info.owner_guid,
                "held_since": self._held_since.isoformat() if lock_info.held_since else None,
            },
            default=str,
        )

    async def _start_heartbeat(self) -> None:
        logging.debug(
            "Starting heartbeat task. "
            f"key={self.key} "
            f"hostname={self.hostname} "
            f"ttl={self.ttl} "
            f"metadata={self.metadata} "
            f"is_permanent={self.is_permanent} "
            f"owner_guid={self._owner_guid}"
        )
        self._heartbeat_task = asyncio.create_task(self._heartbeat())

    async def _stop_heartbeat(self) -> None:
        if self._heartbeat_task:
            logging.debug(
                "Stopping heartbeat task. "
                f"key={self.key} "
                f"hostname={self.hostname} "
                f"ttl={self.ttl} "
                f"metadata={self.metadata} "
                f"is_permanent={self.is_permanent} "
                f"owner_guid={self._owner_guid}"
            )
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def _heartbeat(self) -> None:
        assert self.ttl  # Must be set if heartbeat is alive
        if self.ttl < datetime.timedelta(seconds=5):
            # Anything less than 5 second will result in a significantly heightened risk of losing the lock.
            # Setting sleep interval to 0 means we'll refresh the lock every chance we get.
            sleep_interval = datetime.timedelta(seconds=0)
        else:
            sleep_interval = self.ttl / 2

        while True:
            try:
                await self.refresh()
            except _exceptions.LockIsPermanent:
                # Lock was made permanent, we no longer need to heartbeat.
                return
            except _exceptions.LockNotOwnedByUs:
                logging.warning(
                    "Lock was lost. "
                    "This may have occurred due to blocked CPU blocking us from refreshing the lock. "
                    "If this is happening often, consider increasing the TTL of your locks. "
                    f"key={self.key}"
                )
                return

            await asyncio.sleep(sleep_interval.total_seconds())
