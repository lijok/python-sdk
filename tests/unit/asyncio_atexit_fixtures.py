import asyncio

import pytest
import uvloop

EventLoopPolicies: dict[str, asyncio.AbstractEventLoopPolicy] = {
    "asyncio": asyncio.DefaultEventLoopPolicy,
    "uvloop": uvloop.EventLoopPolicy,
}


@pytest.fixture(scope="function", params=EventLoopPolicies.values(), ids=list(EventLoopPolicies.keys()))
def event_loop_policy(request: pytest.FixtureRequest) -> None:
    old_policy = asyncio.get_event_loop_policy()
    requested_policy = request.param
    asyncio.set_event_loop_policy(policy=requested_policy())
    yield
    asyncio.set_event_loop_policy(policy=old_policy)
