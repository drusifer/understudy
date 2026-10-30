"""The stage library: the functions a sketch's `do:` names (filled in Phase 7)."""

from collections.abc import Awaitable, Callable

StageFn = Callable[..., Awaitable]
LIBRARY: dict[str, StageFn] = {}
