from python_sdk.locks._lock_provider import _protocol


class LockAcquisitionError(Exception):
    ...


class LockTaken(LockAcquisitionError):
    current_lock: _protocol.LockInfo

    def __init__(self, current_lock: _protocol.LockInfo) -> None:
        super().__init__(current_lock)
        self.current_lock = current_lock

    def __str__(self) -> str:
        return self.current_lock.key


class LockNotOwnedByUs(Exception):
    current_lock: _protocol.LockInfo

    def __init__(self, current_lock: _protocol.LockInfo) -> None:
        super().__init__(current_lock)
        self.current_lock = current_lock

    def __str__(self) -> str:
        return self.current_lock.key


class LockIsPermanent(Exception):
    current_lock: _protocol.LockInfo

    def __init__(self, current_lock: _protocol.LockInfo) -> None:
        super().__init__(current_lock)
        self.current_lock = current_lock

    def __str__(self) -> str:
        return self.current_lock.key
