# moonblade
A Python 3 asynchronous library committed to communicating with LOL server through the LCU API in a simple and flexible way.

## Setup

```python
pip install moonblade
```

## Usage

moonblade consists of `MoonBlade`, `Router`, and `Node`.

### MoonBlade

`MoonBlade` is a connector to connect to LOL server.
At the beginning, it is necessary to import the class.
```python
from moonblade import MoonBlade
```

To communicating with LOL server, you need to start MoonBlade first.
```python
mb = MoonBlade()
mb.start()
```

Similarly, when stopping the use of MoonBlade, it is necessary to stop MoonBlade.
```python
mb.stop()
```

MoonBlade is alse support context managers.
```python
async with MoonBlade() as mb:
    ...
    while True:
        await asyncio.sleep(1)
```

### Router

`Router` is used to distribute events received from the LOL server.
Before use, it is also necessary to import the class.
```python
from moonblade import Router
```

#### register

To receive events, we need to register asynchronous handlers.
The handler should be able to accept a dict param.
```python
async def example(data: dict):
    pass

router = Router()
router.register(route = "/moonblade/start", event_type = "All", handler = example)
```
Note that Router is a singleton class that points to the same Router no matter how many times it is instantiated.

Router can also be used without instantiation.
```python
Router.register(route = "/moonblade/start", event_type = "All", handler = example)
```

Router can also be use as a decorator to register route.

```python
@Router.register(route = "/moonblade/start", event_type = "All")
async def example(data: dict):
    pass
```
In fact, I recommend using this way. It should be noted that when registering route with a decorator, the handler param should be `None`.

We can also register asynchronous methods, which will be introduced later.

##### event_type
Including `Create`, `Update`, `Delete` and `All`. Default to `All` and case-insensitive.

#### fake

An asynchronous method to fake an event from the server.
```python
await Router.fake(None, 'Update', '/moonblade/start')
```

### Node

Router can register asynchronous methods. In this situation, the class witch the method in should be a subclass of `Node`.
```python
class C(Node):

    def __init__(self) -> None:
        ...
        super().__init__()

    @Router.register('/moonblade/start')
    async def example(self, data: dict):
        pass
```

Also, we can add `for key in self.__dir__(): getattr(self, key)` to the end of the `__init__` method to achieve the same effect.
```python
class C:
    def __init__(self) -> None:
        for key in self.__dir__():
            getattr(self, key)

    @Router.register('/moonblade/start')
    async def example(self, data: dict):
        pass
```

## Application

For more detailed usage instructions, reference the library [`Diana`](https://github.com/gfk-sveyigey/Diana) witch is based on moonblade.

