from __future__ import annotations

import datetime
import types
import typing

ObjectType: typing.TypeAlias = str | dict[str, typing.Any]


class LockProvider(typing.Protocol):
    hostname: str
    default_ttl: datetime.timedelta
    default_metadata: dict[str, str]
    default_retry_times: int
    default_retry_delay: datetime.timedelta

    def __init__(
        self,
        hostname: str | None,
        default_ttl: datetime.timedelta,
        default_metadata: dict[str, str],
        default_retry_times: int,
        default_retry_delay: datetime.timedelta,
    ) -> None:
        ...

    def lock(
        self,
        key: str,
        object: ObjectType | None = None,
        ttl: datetime.timedelta | None = None,
        additional_metadata: dict[str, str] | None = None,
        retry_times: int | None = None,
        retry_delay: datetime.timedelta | None = None,
    ) -> Lock:
        ...

    def permanent_lock(
        self,
        key: str,
        object: ObjectType | None = None,
        additional_metadata: dict[str, str] | None = None,
        retry_times: int | None = None,
        retry_delay: datetime.timedelta | None = None,
    ) -> Lock:
        ...


class Lock(typing.Protocol):
    key: str
    object: ObjectType | None
    hostname: str
    ttl: datetime.timedelta | None
    metadata: dict[str, str]
    is_permanent: bool
    retry_times: int
    retry_delay: datetime.timedelta

    @property
    async def current_lock(self) -> LockInfo:
        """
        Fetches the state of the current lock.
        """

    async def __aenter__(self) -> Lock:
        """
        Acquires a lock and starts a heartbeat to keep the lock refreshed until it is released.

        Raises:
            LockTaken: This lock has already been acquired by someone else.
        """

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """
        Releases the lock so long as it's still owned by us.
        Will emit a warning if the lock was lost or stolen (acquired by someone else).
        This will not release a lock that was turned permanent.
        """

    async def acquire(self) -> LockInfo:
        """
        Acquires a lock and starts a heartbeat to keep the lock refreshed until it is released.

        Raises:
            LockTaken: This lock is already owned by someone else.
        """

    async def refresh(self) -> LockInfo:
        """
        Refreshes a lock owned by us.
        If a lock that is owned by us is expired at the time of refresh, it will be refreshed given noone else acquired
        the lock, otherwise, will raise LockNotOwnedByUs.
        It is not recommended to use this method directly. It's safer to use the lock as a context manager, which will
        automatically refresh the lock periodically.

        Raises:
            LockIsPermanent: Attempted to refresh a permanent lock.
            LockNotOwnedByUs: Attempted to refresh a lock that's not owned by us.
        """

    async def make_permanent(self) -> LockInfo:
        """
        Turns a temporary lock owned by us permanent.
        This will remove the ttl from the lock.
        This method should only be used when processing objects that must be locked permanently after they are
        successfully processed. For example, you may obtain a temporary lock for a domain event you receive, but then
        turn it permanent if you successfully process the domain event, so that it won't ever be processed again.

        Raises:
            LockNotOwnedByUs: Attempted to turn a temporary lock that's not owned by us permanent.
        """

    # TODO: Clarify what can be released and what can't
    async def release(self) -> None:
        """
        Releases a lock that's either expired or owned by us.
        A lock that is not owned by us may be released so long as it's expired.
        Attempting to release a lock that is permanent will result in the LockIsPermanent exception.
        A lock that is owned by us may be released regardless of whether it's expired or not.
        It is not recommended to use this method directly. It's safer to use the lock as a context manager, which will
        automatically release the lock on exit, unless it was turned permanent, lost or stolen.

        Raises:
            LockNotOwnedByUs: Attempted to release a lock that's not expired and not owned by us.
            LockIsPermanent: Attempted to release a permanent lock.
        """

    async def force_release(self) -> None:
        """
        Releases a lock regardless of whether it's expired, permanent, or owned by us.
        """

    async def _stop_heartbeat(self) -> None:
        """
        A function, for test purposes, to stop any heartbeat task that maybe running.
        This is exposed as an interface only for testing.
        """


class LockInfo:
    key: str
    object: ObjectType | None
    hostname: str | None
    ttl: datetime.timedelta | None
    metadata: dict[str, str] | None
    is_permanent: bool | None
    acquired_at: datetime.datetime | None
    expires_at: datetime.datetime | None
    is_owned_by_me: bool
    exists: bool
    owner_guid: str | None
    held_since: datetime.datetime | None

    def __init__(
        self,
        key: str,
        object: ObjectType | None,
        hostname: str | None,
        ttl: datetime.timedelta | None,
        metadata: dict[str, str] | None,
        is_permanent: bool | None,
        acquired_at: datetime.datetime | None,
        expires_at: datetime.datetime | None,
        is_owned_by_me: bool,
        exists: bool,
        owner_guid: str | None,
        held_since: datetime.datetime | None,
    ) -> None:
        self.key = key
        self.object = object
        self.hostname = hostname
        self.ttl = ttl
        self.metadata = metadata
        self.is_permanent = is_permanent
        self.acquired_at = acquired_at
        self.expires_at = expires_at
        self.is_owned_by_me = is_owned_by_me
        self.exists = exists
        self.owner_guid = owner_guid
        self.held_since = held_since

    @property
    def expires_in(self) -> datetime.timedelta | None:
        if self.expires_at is None:
            return None
        return self.expires_at - datetime.datetime.now(tz=datetime.timezone.utc)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.datetime.now(tz=datetime.timezone.utc) > self.expires_at

    @property
    def held_for(self) -> datetime.timedelta | None:
        if self.held_since is None:
            return None
        return datetime.datetime.now(tz=datetime.timezone.utc) - self.held_since
