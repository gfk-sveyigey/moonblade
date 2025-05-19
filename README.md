# moonblade
An asynchronous Python 3 library designed to communicate with the LOL server via the LCU API in a simple and flexible way.

## Setup

```python
pip install moonblade
```

## Usage

`moonblade` consists of three core components: `MoonBlade`, `Router`, and `Node`.

### MoonBlade

`MoonBlade` is a connector for establishing communication with the LOL server.
Before using it, you need to import the class:
```python
from moonblade import MoonBlade
```

To start communication with the LOL server, create an instance of `MoonBlade` and call `start()`:
```python
mb = MoonBlade()
await mb.start()
```

To stop communication:
```python
await mb.stop()
```

`MoonBlade` also supports use as an asynchronous context manager:
```python
async with MoonBlade() as mb:
    ...
    while True:
        await asyncio.sleep(1)
```

### Router

`Router` is responsible for dispatching events received from the LOL server.
Before using it, import the class:
```python
from moonblade import Router
```

#### register
To receive events, you need to register asynchronous handlers.
The `register` function accepts three parameters: `route`, `event_types`, and `handler`.

##### route
A route can be a URI or a path.
If the route ends with a `"/"`, it is treated as a path; otherwise, as a URI.
Additionally, `moonblade` exposes the URI `"/moonblade"`, which dispatches:
A `Create` event when a connection to the LOL service is successfully established;
A `Delete` event when the connection is lost;
No `Update` event is dispatched for this URI.

##### event_types
Accepts one of the strings `Create`, `Update`, `Delete`, or `All`, or an iterable containing any combination of these strings.
Defaults to "All". Case-insensitive.

##### handler
The handler must be an asynchronous function that accepts a single `dict`.
``` python
async def example(data: dict):
    pass
```

You can create a `Router` instance and register a route:
```python
router = Router()
router.register(route = "/moonblade", event_types = "Create", handler = example)
```
Note: `Router` is a singleton. All instances refer to the same underlying object.

You can also register without instantiating:
```python
Router.register(route = "/moonblade", event_types = ("Create",), handler = example)
```

Or use the decorator style (recommended).
When using the decorator, you **must omit** the `handler` parameter:
```python
@Router.register(route = "/moonblade", event_types = ["Create"])
async def example(data: dict):
    pass
```

`Router` also supports registering asynchronous class methods, described below.

#### unregister
You can `unregister` a previously registered `handler`:
``` python
router.unregister(route = "/moonblade", event_types = {"Create"}, handler = example)
```
If `handler` is set to `None`, all handlers for the specified route and event types will be unregistered.

#### fake

You can simulate events from the server using the asynchronous `fake` method:
```python
await Router.fake(data = None, event_type = 'Create', uri = '/moonblade')
await Router.fake(data = None, event_type = 'Delete', uri = '/moonblade')
```

### Node

You can also register asynchronous class methods as event handlers.
In this case, the class must inherit from `Node`:
```python
class N(Node):

    def __init__(self) -> None:
        ...
        super().__init__()

    @Router.register('/moonblade', 'Create')
    async def moonblade_start(self, data: dict):
        pass
```

Alternatively, if not inheriting from `Node`, you can trigger handler registration by iterating over `__dir__()`:
```python
class N:
    def __init__(self) -> None:
        for key in self.__dir__():
            getattr(self, key)

    @Router.register('/moonblade', 'Delete')
    async def moonblade_stop(self, data: dict):
        pass
```

## Application

For more detailed usage instructions, reference the library [`Diana`](https://github.com/gfk-sveyigey/Diana) which is built on top of `moonblade`.

