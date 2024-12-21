import asyncio
import functools
from types import MethodType
from typing import Callable, Iterable


class Node:
    """
    When registering a class method, the class in which the method is located must 
    be a subclass of the ``Node``.
    """
    def __init__(cls) -> None:
        """
        Traverse properties to ensure that all decorated methods are bound to instances.
        """
        for key in cls.__dir__():
            getattr(cls, key)


class _Handler:
    """
    Used to register class methods.
    """
    def __init__(self, f):
        self.f = f
        self.m = None
        functools.update_wrapper(self, f)

    def __get__(self, obj, objtype) -> Callable:
        """
        Bind methods and instances when accessed as class variables.
        """
        if obj is not None:
            self.m = MethodType(self.f, obj)
        return self.m
    
    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs) if self.m is None else self.m(*args, **kwargs)


class Router(object):
    """
    For distributing events.

    For more detailed usage instructions, reference the library based on MoonBlade
    `https://github.com/gfk-sveyigey/Diana`
    """

    registered_uris: dict[str:list] = {}
    registered_paths: dict[str:list] = {}
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
        event_type: str | Iterable[str] = "All",
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
        :return: None

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
        
        if len(event_type) == 0:
            event_type = "All"
        if "All" in event_type:
            event_type = ("Create", "Update", "Delete")

        if isinstance(event_type, str):
            event_type = (event_type.capitalize(), )
        else:
            event_type = [i.capitalize() for i in event_type]

        def decorator(handler_: Callable) -> Callable:
            if not asyncio.iscoroutinefunction(handler_):
                raise TypeError("The handler must be asynchronous.")
            
            if not hasattr(handler_, "__func__"):
                handler_ = _Handler(handler_)

            registered = cls.registered_paths if route.endswith("/") else cls.registered_uris

            if route not in registered.keys():
                registered[route] =[]
            event = {"handler": handler_, "event_type": event_type}
            registered[route].append(event)
            return handler_
        
        if handler is None:
            return decorator
        else:
            return decorator(handler)

    @classmethod
    async def fake(cls, data, event_type: str, uri: str):
        """
        Fake a message published by a server.

        :param data: The data dict or None.
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

        data = {"data": data, "eventType": event_type, "uri": uri}
        await Router._dispatch(data)

    @classmethod
    async def _dispatch(cls, data: dict):

        if data is None:
            return
        uri: str = data["uri"]
        event_type: str = data["eventType"].capitalize()

        if uri in cls.registered_uris.keys():
            for event in cls.registered_uris[uri]:
                if event_type in event["event_type"]:
                    handler = event["handler"]
                    await handler(data)

        for path in cls.registered_paths.keys():
            if uri.startswith(path):
                for event in cls.registered_paths[path]:
                    if event_type in event["event_type"]:
                        handler = event["handler"]
                        await handler(data)
        return
