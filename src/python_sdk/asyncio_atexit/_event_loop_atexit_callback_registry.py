from __future__ import annotations

import asyncio
import typing
import weakref

from python_sdk.asyncio_atexit import _callback

_event_loop_atexit_callback_registry: weakref.WeakKeyDictionary[
    asyncio.AbstractEventLoop, EventLoopAtexitCallbackRegistryEntry
] = weakref.WeakKeyDictionary()


def _get_entry(loop: asyncio.AbstractEventLoop) -> EventLoopAtexitCallbackRegistryEntry | None:
    try:
        return _event_loop_atexit_callback_registry[loop]
    except KeyError:
        return None


def _add_entry(entry: EventLoopAtexitCallbackRegistryEntry) -> None:
    _event_loop_atexit_callback_registry[entry.loop] = entry


class EventLoopAtexitCallbackRegistryEntry:
    """
    Holds and event loop and its registered atexit callbacks.
    """

    loop: asyncio.AbstractEventLoop
    callbacks: list[tuple[_callback.Callback, tuple[typing.Any, ...], dict[str, typing.Any]]]
    _original_close_method_getter: weakref.WeakMethod[typing.Any] | typing.Callable[[], typing.Callable[[], typing.Any]]

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

        # Avoid double-patching.
        # As we're using weakrefs, they can get unresolved and then close called in __del__.
        if not hasattr(loop, "_atexit_original_close_method"):
            # Back up original loop close method.
            setattr(loop, "_atexit_original_close_method", loop.close)

        try:
            self._original_close_method_getter = weakref.WeakMethod(getattr(loop, "_atexit_original_close_method"))
        except TypeError:
            # Not everything can be weakref'd (Extensions such as uvloop).
            # Hold a regular reference on the object, in those cases.
            self._original_close_method_getter = lambda: getattr(loop, "_atexit_original_close_method")

        self.callbacks = []

    def add_callback(
        self,
        callback: _callback.Callback,
        *callback_args: typing.Any,
        **callback_kwargs: typing.Any,
    ) -> None:
        self.callbacks.append((callback, callback_args, callback_kwargs))

    def remove_callback(self, callback: _callback.Callback) -> None:
        self.callbacks = [
            registered_callback for registered_callback in self.callbacks if registered_callback[0] != callback
        ]

    @property
    def original_close_method(self) -> typing.Any:
        return self._original_close_method_getter()


def register(loop: asyncio.AbstractEventLoop) -> EventLoopAtexitCallbackRegistryEntry:
    """
    Idempotent registration mechanism.
    Args:
        loop: Loop to register.
    """
    if existing_entry := _get_entry(loop):
        return existing_entry

    entry = EventLoopAtexitCallbackRegistryEntry(loop=loop)
    _add_entry(entry=entry)
    return entry
