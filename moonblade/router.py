import asyncio
import functools
import threading

from collections import defaultdict
from types import MethodType
from typing import Callable, Iterable


class Node:
    """
    When registering a class method, the class in which the method is located must 
    be a subclass of the ``Node``.
    """
    def __init__(cls) -> None:
        for key in cls.__dir__():
            getattr(cls, key)


class HandlerRegistry:
    
    def __init__(self):
        self._data: dict[str, list[dict[str, Callable | set[str]]]] = defaultdict(list)
        self._lock = threading.RLock()
        self.__slots__ = ("_data", "_lock")
        self.__all__ = ["register_handler", "unregister_handler", "get_handlers"]

    def register_handler(self, route: str, handler: Callable, event_types: Iterable[str] | str) -> None:
        with self._lock:
            if isinstance(event_types, str):
                event_types = {event_types.capitalize()}
            else:
                event_types = {i.capitalize() for i in event_types}

            for entry in self._data[route]:
                if entry["handler"] == handler:
                    entry["event_types"].update(event_types)
                    return
            self._data[route].append({"handler": handler, "event_types": set(event_types)})

    def unregister_handler(self, route: str, handler: Callable | None, event_types: Iterable[str] | str) -> None:
        with self._lock:
            if isinstance(event_types, str):
                event_types = {event_types.capitalize()}
            else:
                event_types = {i.capitalize() for i in event_types}

            new_list = []
            for entry in self._data.get(route, []):
                if handler is None or entry["handler"] == handler:
                    entry["event_types"].difference_update(event_types)
                    if entry["event_types"]:
                        new_list.append(entry)
                else:
                    new_list.append(entry)
            if new_list:
                self._data[route] = new_list
            else:
                self._data.pop(route, None)

    def get_handlers(self, route: str, event_type: str) -> list[Callable]:
        with self._lock:
            handlers = []
            event_type = event_type.capitalize()

            for registered_uri, entries in self._data.items():
                route_matched = (
                    route.startswith(registered_uri) 
                    if registered_uri.endswith("/") 
                    else route == registered_uri
                )

                if route_matched:
                    handlers.extend(
                        entry["handler"] 
                        for entry in entries 
                        if event_type in entry["event_types"]
                    )

            return handlers


class _Handler:
    def __init__(self, f):
        self.f = f
        self.m = None
        functools.update_wrapper(self, f)

    def __get__(self, obj, objtype) -> Callable:
        if obj is None:
            self.m = None
        else:
            self.m = MethodType(self.f, obj)
        return self.m
    
    def __call__(self, *args, **kwargs):
        if self.m is None:
            return self.f(*args, **kwargs)
        else:
            return self.m(*args, **kwargs)


class Router(object):
    """
    For distributing events.

    For more detailed usage instructions, reference the library based on MoonBlade
    `https://github.com/gfk-sveyigey/Diana`
    """

    registered_uris: dict[str: list[dict[str: Callable], dict[str: Iterable[str]]]] = {}
    registered_paths: dict[str: list] = {}
    handler_registry = HandlerRegistry()
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Implement Singleton.
        """

        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def register(
        cls,
        route: str = "/",
        event_types: str | Iterable[str] = "All",
        handler: Callable | None = None,
    ) -> Callable | None:
        """
        Register a asynchronous method or function as handler with the given route.

        The method can be explicitly called or called as a decorator.
        
        When decorating a method, the class which the method in should be a subclass 
        of ``Node``.

        The `route` parameter supports path or uri. Register the route as a path 
        if it is end with "/" else as a uri.

        The handler needs to be able to accept the `data` parameter.

        :param route: The route string.
        :param event_type: Case insensitive. `Create`, `Update`, `Delete`, `All`,
        or an Iterable containing several parameters like `(Create, Update)`.
        :param handler: When explicitly calling the method, handler is needed, 
        and when the function is called as a decorator, handler need to be ``None``.
        :return: When explicitly calling the method, return ``None``, and when 
        the function is called as a decorator, return callable decorator.

        Example:
        .. code-block:: python
            @Router.register("/lol-chat/v1/me", "All")
            async def on_chat_event(data):
                return

            Router.register("/lol-chat/v1/me", "All", handler)

        """

        if route == "":
            raise ValueError("Route cannot be empty string.")
        elif not route.startswith('/'):
            raise ValueError("Route must start with \"/\"")

        if len(event_types) == 0:
            event_types = "All"
        if "All" in event_types:
            event_types = ("Create", "Update", "Delete")

        def decorator(handler_: Callable) -> Callable:
            if not asyncio.iscoroutinefunction(handler_):
                raise TypeError("The handler must be asynchronous.")
            
            if not hasattr(handler_, "__func__"):
                handler_ = _Handler(handler_)

            cls.handler_registry.register_handler(route, handler_, event_types)
            return handler_
        
        if handler is None:
            return decorator
        else:
            decorator(handler)
            return None

    @classmethod
    def unregister(
        cls,
        route: str = "/",
        event_types: str | Iterable[str] = "All",
        handelr: Callable | None = None,
    ) -> None:
        
        if route == "":
            raise ValueError("Route cannot be empty string.")
        elif not route.startswith('/'):
            raise ValueError("Route must start with \"/\"")
        
        if len(event_types) == 0:
            event_types = "All"
        if "All" in event_types:
            event_types = ("Create", "Update", "Delete")

        cls.handler_registry.unregister_handler(route, handelr, event_types)


    @classmethod
    async def fake(cls, data, event_type: str, uri: str):
        """
        Fake a message published by a server.

        :param data: The data that needs to be dispatched.
        :param event_type: The EventType string, possible values: ``Create``, 
        ``Update``, ``Delete``.
        :param uri: The uri string.
        :return: None

        Example:
        .. code-block:: python
            await Router.fake(
                data = None, 
                event_type = "Update", 
                uri = "/lol-chat/v1/me"
            )
        """

        event_type = event_type.capitalize()
        if event_type not in ["Create", "Update", "Delete"]:
            raise Exception
        data = {"data": data, "eventType": event_type, "uri": uri}
        await Router._dispatch(data)

    @classmethod
    async def _dispatch(cls, data: dict):

        if data is None:
            return
        uri: str = data["uri"]
        event_type: str = data["eventType"]

        handlers = cls.handler_registry.get_handlers(uri, event_type)
        handlers = [handler(data) for handler in handlers]
        asyncio.gather(*handlers)
        return
