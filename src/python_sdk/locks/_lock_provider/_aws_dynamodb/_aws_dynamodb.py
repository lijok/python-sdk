from __future__ import annotations

import asyncio
import datetime
import decimal
import logging
import socket
import types
import typing
import uuid

import boto3.dynamodb.types
import botocore.exceptions

from python_sdk.locks._lock_provider import _exceptions
from python_sdk.locks._lock_provider import _protocol

if typing.TYPE_CHECKING:
    import mypy_boto3_dynamodb


class AWSDynamoDBLockProvider:
    """
    Implements a lock provider using AWS DynamoDB.

    Note that AWS DynamoDB records can only be up to 400KB in size. Avoid creating locks with large objects.
    """

    hostname: str
    default_ttl: datetime.timedelta
    default_metadata: dict[str, str]
    default_retry_times: int
    default_retry_delay: datetime.timedelta
    _aws_dynamodb_client: mypy_boto3_dynamodb.DynamoDBClient
    table_name: str
    partition_key: str
    object_key: str

    def __init__(
        self,
        hostname: str | None,
        default_ttl: datetime.timedelta,
        default_metadata: dict[str, str],
        default_retry_times: int,
        default_retry_delay: datetime.timedelta,
        aws_dynamodb_client: mypy_boto3_dynamodb.DynamoDBClient,
        table_name: str,
        partition_key: str,
        object_key: str,
    ) -> None:
        self.hostname = hostname or socket.gethostname()
        self.default_ttl = default_ttl
        self.default_metadata = default_metadata or {}
        self.default_retry_times = default_retry_times
        self.default_retry_delay = default_retry_delay
        self._aws_dynamodb_client = aws_dynamodb_client
        self.table_name = table_name
        self.partition_key = partition_key
        self.object_key = object_key

    def lock(
        self,
        key: str,
        object: _protocol.ObjectType | None = None,
        ttl: datetime.timedelta | None = None,
        additional_metadata: dict[str, str] | None = None,
        retry_times: int | None = None,
        retry_delay: datetime.timedelta | None = None,
    ) -> AWSDynamoDBLock:
        ttl = ttl if ttl is not None else self.default_ttl
        metadata = self.default_metadata | (additional_metadata or {})

        return AWSDynamoDBLock(
            key=key,
            object=object,
            hostname=self.hostname,
            ttl=ttl,
            metadata=metadata,
            is_permanent=False,
            retry_times=retry_times or self.default_retry_times,
            retry_delay=retry_delay or self.default_retry_delay,
            aws_dynamodb_client=self._aws_dynamodb_client,
            table_name=self.table_name,
            partition_key=self.partition_key,
            object_key=self.object_key,
        )

    def permanent_lock(
        self,
        key: str,
        object: _protocol.ObjectType | None = None,
        additional_metadata: dict[str, str] | None = None,
        retry_times: int | None = None,
        retry_delay: datetime.timedelta | None = None,
    ) -> AWSDynamoDBLock:
        metadata = self.default_metadata | (additional_metadata or {})

        return AWSDynamoDBLock(
            key=key,
            object=object,
            hostname=self.hostname,
            ttl=None,
            metadata=metadata,
            is_permanent=True,
            retry_times=retry_times or self.default_retry_times,
            retry_delay=retry_delay or self.default_retry_delay,
            aws_dynamodb_client=self._aws_dynamodb_client,
            table_name=self.table_name,
            partition_key=self.partition_key,
            object_key=self.object_key,
        )


class AWSDynamoDBLock:
    key: str
    object: _protocol.ObjectType | None
    hostname: str
    ttl: datetime.timedelta | None
    metadata: dict[str, str]
    is_permanent: bool
    retry_times: int
    retry_delay: datetime.timedelta
    _aws_dynamodb_client: mypy_boto3_dynamodb.DynamoDBClient
    table_name: str
    partition_key: str
    object_key: str
    _owner_guid: str
    _heartbeat_task: asyncio.Task[None] | None
    _held_since: datetime.datetime | None

    def __init__(
        self,
        key: str,
        object: _protocol.ObjectType | None,
        hostname: str,
        ttl: datetime.timedelta | None,
        metadata: dict[str, str],
        is_permanent: bool,
        retry_times: int,
        retry_delay: datetime.timedelta,
        aws_dynamodb_client: mypy_boto3_dynamodb.DynamoDBClient,
        table_name: str,
        partition_key: str,
        object_key: str,
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
        self._aws_dynamodb_client = aws_dynamodb_client
        self.table_name = table_name
        self.partition_key = partition_key
        self.object_key = object_key
        self._owner_guid = str(uuid.uuid4())
        self._heartbeat_task = None
        self._held_since = None

    @property
    async def current_lock(self) -> _protocol.LockInfo:
        response = await asyncio.to_thread(
            self._aws_dynamodb_client.get_item,
            TableName=self.table_name,
            Key={self.partition_key: {"S": self.key}},
            ConsistentRead=True,
        )
        if "Item" not in response or not response["Item"]:
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

        return self._aws_dynamodb_item_to_lock_info(item=response["Item"])

    async def __aenter__(self) -> AWSDynamoDBLock:
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
            # Lock was made permanent while we were in the context manager, this is fine.
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

        raise RuntimeError()  # Not reachable

    async def _acquire(self) -> _protocol.LockInfo:
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

        try:
            await asyncio.to_thread(
                self._aws_dynamodb_client.put_item,
                TableName=self.table_name,
                Item=self._lock_info_to_aws_dynamodb_record(lock_info=new_lock),
                ConditionExpression=(
                    "attribute_not_exists(LockID) OR "
                    "(expires_at < :current_datetime AND is_permanent = :is_permanent)"
                ),
                ExpressionAttributeValues={
                    ":is_permanent": {"BOOL": False},
                    ":current_datetime": {"S": datetime.datetime.now(tz=datetime.timezone.utc).isoformat()},
                },
            )
        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ConditionalCheckFailedException":
                logging.debug(f"Failed to acquire lock. Lock taken. key={new_lock.key}")
                # TODO: When DynamoDB-Local implements support for ReturnValuesOnConditionCheckFailure, we can
                # deserialize current lock from e.response["Item"].
                raise _exceptions.LockTaken(current_lock=await self.current_lock) from e
            elif error_code == "ProvisionedThroughputExceededException":
                logging.warning(
                    "Hit DynamoDB ProvisionedThroughputExceededException. "
                    "Consider increasing provisioned throughput or transition to an on-demand throughput type."
                )
                raise
            else:
                raise

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
            f"held_since={new_lock.held_since} "
        )

        if not new_lock.is_permanent:
            await self._start_heartbeat()

        return new_lock

    async def refresh(self) -> _protocol.LockInfo:
        if self.is_permanent:
            raise _exceptions.LockIsPermanent(current_lock=await self.current_lock)

        new_lock = self._new_lock_info
        assert new_lock.owner_guid  # mypy hint

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

        try:
            await asyncio.to_thread(
                self._aws_dynamodb_client.put_item,
                TableName=self.table_name,
                Item=self._lock_info_to_aws_dynamodb_record(lock_info=new_lock),
                ConditionExpression="owner_guid = :owner_guid",
                ExpressionAttributeValues={
                    ":owner_guid": {"S": new_lock.owner_guid},
                },
            )
        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ConditionalCheckFailedException":
                # TODO: When DynamoDB-Local implements support for ReturnValuesOnConditionCheckFailure, we can
                # deserialize current lock from e.response["Item"].
                raise _exceptions.LockNotOwnedByUs(current_lock=await self.current_lock) from e
            elif error_code == "ProvisionedThroughputExceededException":
                logging.warning(
                    "Hit DynamoDB ProvisionedThroughputExceededException. "
                    "Consider increasing provisioned throughput or transition to an on-demand throughput type."
                )
                raise
            else:
                raise

        logging.debug(
            "Lock refreshed. "
            f"key={new_lock.key} "
            f"hostname={new_lock.hostname} "
            f"ttl={new_lock.ttl} "
            f"metadata={new_lock.metadata} "
            f"is_permanent={new_lock.is_permanent} "
            f"acquired_at={new_lock.acquired_at} "
            f"expires_at={new_lock.expires_at} "
            f"owner_guid={new_lock.owner_guid} "
            f"held_since={new_lock.owner_guid}"
        )

        return new_lock

    async def make_permanent(self) -> _protocol.LockInfo:
        await self._stop_heartbeat()
        self.is_permanent = True
        self.ttl = None

        new_lock = self._new_lock_info
        assert new_lock.owner_guid  # mypy hint

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

        try:
            await asyncio.to_thread(
                self._aws_dynamodb_client.put_item,
                TableName=self.table_name,
                Item=self._lock_info_to_aws_dynamodb_record(lock_info=new_lock),
                ConditionExpression="owner_guid = :owner_guid",
                ExpressionAttributeValues={
                    ":owner_guid": {"S": new_lock.owner_guid},
                },
            )
        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ConditionalCheckFailedException":
                # TODO: When DynamoDB-Local implements support for ReturnValuesOnConditionCheckFailure, we can
                # deserialize current lock from e.response["Item"].
                raise _exceptions.LockNotOwnedByUs(current_lock=await self.current_lock) from e
            elif error_code == "ProvisionedThroughputExceededException":
                logging.warning(
                    "Hit DynamoDB ProvisionedThroughputExceededException. "
                    "Consider increasing provisioned throughput or transition to an on-demand throughput type."
                )
                raise
            else:
                raise

        logging.debug(
            "Lock made permanent. "
            f"key={new_lock.key} "
            f"hostname={new_lock.hostname} "
            f"ttl={new_lock.ttl} "
            f"metadata={new_lock.metadata} "
            f"is_permanent={new_lock.is_permanent} "
            f"acquired_at={new_lock.acquired_at} "
            f"expires_at={new_lock.expires_at} "
            f"owner_guid={new_lock.owner_guid}"
            f"held_since={new_lock.held_since} "
        )

        return new_lock

    async def release(self) -> None:
        await self._stop_heartbeat()

        logging.debug(f"Releasing lock. key={self.key}")

        try:
            await asyncio.to_thread(
                self._aws_dynamodb_client.delete_item,
                TableName=self.table_name,
                Key={self.partition_key: {"S": self.key}},
                ConditionExpression="owner_guid = :owner_guid AND is_permanent = :is_permanent",
                ExpressionAttributeValues={
                    ":owner_guid": {"S": self._owner_guid},
                    ":is_permanent": {"BOOL": False},
                },
            )
        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logging.warning(f"Lock was released by another process. key={self.key}")
                return
            if error_code == "ConditionalCheckFailedException":
                # Normally we could check the returned Item, however, dynamodb-local currently does not implement
                # ReturnValuesOnConditionCheckFailure, and therefore, we must fetch the lock for the check.

                # TODO: When DynamoDB-Local implements support for ReturnValuesOnConditionCheckFailure, we can
                # deserialize current lock from e.response["Item"].
                current_lock = await self.current_lock
                if current_lock.is_permanent:
                    raise _exceptions.LockIsPermanent(current_lock=current_lock) from e
                else:
                    raise _exceptions.LockNotOwnedByUs(current_lock=current_lock) from e
            elif error_code == "ProvisionedThroughputExceededException":
                logging.warning(
                    "Hit DynamoDB ProvisionedThroughputExceededException. "
                    "Consider increasing provisioned throughput or transition to an on-demand throughput type."
                )
                raise
            else:
                raise

        logging.debug(f"Lock released. key={self.key}")
        return

    async def force_release(self) -> None:
        await self._stop_heartbeat()
        logging.debug(f"Force releasing lock. key={self.key}")

        try:
            await asyncio.to_thread(
                self._aws_dynamodb_client.delete_item,
                TableName=self.table_name,
                Key={self.partition_key: {"S": self.key}},
            )
        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "ResourceNotFoundException":
                logging.warning(f"Lock was released by another process. key={self.key}")
                return

            if error_code == "ProvisionedThroughputExceededException":
                logging.warning(
                    "Hit DynamoDB ProvisionedThroughputExceededException. "
                    "Consider increasing provisioned throughput or transition to an on-demand throughput type."
                )
                raise

            else:
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
            expires_at=now + self.ttl if self.ttl else None,
            is_owned_by_me=True,
            exists=True,
            owner_guid=self._owner_guid,
            held_since=self._held_since,
        )

    def _lock_info_to_aws_dynamodb_record(self, lock_info: _protocol.LockInfo) -> dict[str, typing.Any]:
        data = {
            self.partition_key: lock_info.key,
            self.object_key: lock_info.object,
            "hostname": lock_info.hostname,
            "ttl": decimal.Decimal(str(lock_info.ttl.total_seconds())) if lock_info.ttl else None,
            "metadata": lock_info.metadata,
            "is_permanent": lock_info.is_permanent,
            "acquired_at": lock_info.acquired_at.isoformat() if lock_info.acquired_at else None,
            "expires_at": lock_info.expires_at.isoformat() if lock_info.expires_at else None,
            "owner_guid": lock_info.owner_guid,
            "held_since": lock_info.held_since.isoformat() if lock_info.held_since else None,
        }

        serializer = boto3.dynamodb.types.TypeSerializer()
        return {k: serializer.serialize(v) for k, v in data.items()}

    def _aws_dynamodb_item_to_lock_info(self, item: dict[str, typing.Any]) -> _protocol.LockInfo:
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        data = {k: deserializer.deserialize(v) for k, v in item.items()}

        return _protocol.LockInfo(
            key=data[self.partition_key],
            object=data[self.object_key],
            hostname=data["hostname"],
            ttl=datetime.timedelta(seconds=float(data["ttl"])) if data["ttl"] else None,
            metadata=data["metadata"],
            is_permanent=data["is_permanent"],
            acquired_at=datetime.datetime.fromisoformat(data["acquired_at"]) if data["acquired_at"] else None,
            expires_at=datetime.datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            is_owned_by_me=data["owner_guid"] == self._owner_guid,
            exists=True,
            owner_guid=data["owner_guid"],
            held_since=datetime.datetime.fromisoformat(data["held_since"]),
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
