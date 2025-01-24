from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import Executor
from contextvars import copy_context
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import ParamSpec, TypedDict


Callbacks = Optional[Union[List, Any]]


class RunnableConfig(TypedDict, total=False):
    """Configuration for a Runnable."""

    tags: List[str]
    """
    Tags for this call and any sub-calls (eg. a chain calling an LLM).
    You can use these to filter calls.
    """

    metadata: Dict[str, Any]
    """
    Metadata for this call and any sub-calls (eg. a chain calling an LLM).
    Keys should be strings, values should be JSON-serializable.
    """

    callbacks: Callbacks
    """
    Callbacks for this call and any sub-calls (eg. a chain calling an LLM).
    Tags are passed to all callbacks, metadata is passed to handle*Start callbacks.
    """

    run_name: str
    """
    Name for the tracer run for this call. Defaults to the name of the class.
    """

    max_concurrency: Optional[int]
    """
    Maximum number of parallel calls to make. If not provided, defaults to 
    ThreadPoolExecutor's default.
    """

    recursion_limit: int
    """
    Maximum number of times a call can recurse. If not provided, defaults to 25.
    """

    configurable: Dict[str, Any]
    """
    Runtime values for attributes previously made configurable on this Runnable,
    or sub-Runnables, through .configurable_fields() or .configurable_alternatives().
    Check .output_schema() for a description of the attributes that have been made 
    configurable.
    """

    run_id: Optional[uuid.UUID]
    """
    Unique identifier for the tracer run for this call. If not provided, a new UUID
        will be generated.
    """


P = ParamSpec("P")
T = TypeVar("T")


async def run_in_executor(
    executor_or_config: Optional[Union[Executor, RunnableConfig]],
    func: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """Run a function in an executor.

    Args:
        executor (Executor): The executor.
        func (Callable[P, Output]): The function.
        *args (Any): The positional arguments to the function.
        **kwargs (Any): The keyword arguments to the function.

    Returns:
        Output: The output of the function.
    """
    if executor_or_config is None or isinstance(executor_or_config, dict):
        # Use default executor with context copied from current context
        return await asyncio.get_running_loop().run_in_executor(
            None,
            cast(Callable[..., T], partial(copy_context().run, func, *args, **kwargs)),
        )

    return await asyncio.get_running_loop().run_in_executor(
        executor_or_config, partial(func, **kwargs), *args
    )
