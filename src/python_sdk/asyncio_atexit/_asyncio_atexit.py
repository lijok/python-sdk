import asyncio
import functools
import inspect
import sys
import typing

from python_sdk.asyncio_atexit import _callback
from python_sdk.asyncio_atexit import _event_loop_atexit_callback_registry


def register(
    func: _callback.Callback,
    *args: typing.Any,
    loop: asyncio.AbstractEventLoop | None = None,
    **kwargs: typing.Any,
) -> _callback.Callback:
    """
    Register a function to be executed when the current event loop closes.
    `loop` may be specified to attach a non-running event loop.

    Args:
        func: Function to be called on event loop close
        loop: Non-running event loop to attach function to.
        *args: Optional arguments to pass to func
        **kwargs: Optional keyword arguments to pass to func

    Returns:
        func: Returned to facilitate usage as a decorator.
    """
    entry = _register_event_loop(loop=loop or asyncio.get_running_loop())
    entry.add_callback(func, *args, **kwargs)
    return func


def unregister(
    func: _callback.Callback,
    loop: asyncio.AbstractEventLoop | None = None,
) -> None:
    """
    Unregister an exit function which was previously registered using asyncio_atexit.register
    `loop` may be specified to unregister from a non-running event loop.
    """
    entry = _register_event_loop(loop=loop or asyncio.get_running_loop())
    entry.remove_callback(callback=func)


def _register_event_loop(
    loop: asyncio.AbstractEventLoop,
) -> _event_loop_atexit_callback_registry.EventLoopAtexitCallbackRegistryEntry:
    entry = _event_loop_atexit_callback_registry.register(loop=loop)
    # Patch loop.close method.
    setattr(loop, "close", functools.partial(_close_event_loop, loop))
    return entry


def _close_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    entry = _register_event_loop(loop)
    if entry.callbacks:
        loop.run_until_complete(_run_event_loop_atexit_callbacks(entry=entry))
    entry.callbacks = []
    entry.original_close_method()


async def _run_event_loop_atexit_callbacks(
    entry: _event_loop_atexit_callback_registry.EventLoopAtexitCallbackRegistryEntry,
) -> None:
    for callback, callback_args, callback_kwargs in entry.callbacks:
        try:
            maybe_awaitable = callback(*callback_args, **callback_kwargs)
            if inspect.isawaitable(maybe_awaitable):
                await maybe_awaitable
        except Exception as e:
            print(f"Unhandled exception in asyncio atexit callback {callback}: {e}", file=sys.stderr)
