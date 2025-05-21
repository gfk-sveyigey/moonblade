from .moonblade import MoonBlade, EventCode
from .router import Router, Node

__title__ = "moonblade"
__description__ = "An asynchronous Python 3 library designed to communicate with the LOL server via the LCU API in a simple and flexible way."
__version__ = "1.1.3"
__author__ = "gfk-sveyigey"
__author_email__ = "gfk_sveyigey@163.com"
__url__ = "https://github.com/gfk-sveyigey/moonblade"


__all__ = [
    "__title__",
    "__description__",
    "__version__",
    "MoonBlade",
    "EventCode",
    "Router",
    "Node",
]