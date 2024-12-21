import asyncio
import json
import ssl
from enum import IntEnum

import httpx
import websockets

from .logger import logger
from .router import Router
from .utils import find_LCU_process, parse_LCU_cmdline, build_auth_header


__all__ = [
    "MoonBlade",
    "EventCode",
]


class MoonBlade(object):
    """
    A Python 3 asynchronous library committed to communicating with LOL server through the LCU API in a simple and flexible way .
    """

    __all__ = ["start", "stop", "request"]

    _pid = 0
    _port = 0
    _token = ""
    _http_alive = False
    _ws_alive = False
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()
        return True

    async def start(self):
        logger.info("Starting MoonBlade.")
        LCU_process = find_LCU_process()
        while not LCU_process:
            logger.warning("No running LCUxprocess, re-searching...")
            LCU_process = find_LCU_process()
            await asyncio.sleep(0.5)
        logger.info(f"Found LCUx process.")

        LCU_args = parse_LCU_cmdline(LCU_process.cmdline())
        self._pid = LCU_process.pid
        self._port = int(LCU_args["app-port"])
        self._token = LCU_args["remoting-auth-token"]
        
        await self._start_http()

        await self._start_ws()

        #  Fake subscription message to prompt MoonBlade is fully started.
        await Router.fake(None, "Update", "/moonblade/start")

        logger.info("MoonBlade is fully started.")
        return

    async def _start_http(self):
        if self._http_alive:
            logger.warning("Http is already run.")
            return
        
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self._http_client = httpx.AsyncClient(
            base_url = f"https://127.0.0.1:{self._port}",
            auth = httpx.BasicAuth("riot", self._token),
            headers = headers,
            verify = False
        )
        self._http_alive = True

        while True:
            try:
                res = await self._http_client.get("/riotclient/ux-state")
                if res.status_code == 200:
                    logger.info(f"Connected to LCUx http server.")
                else:
                    logger.warning(f"Connected to LCUx http server, but got an invalid response for a known uri. Status: {res.status_code}")
                break
            except httpx.ConnectError:
                logger.warning(f"Cannot connect to LCUx http server, retrying...")
                await asyncio.sleep(0.5)
                
        logger.info("Http is started.")
        return
    
    async def _start_ws(self):
        if self._ws_alive:
            logger.warning("Ws is already run.")
            return
        
        headers = [
            ("Content-Type", "application/json"),
            ("Accept", "application/json"),
            ("Accept-Encoding", "gzip, deflate"),
            ("Authorization", build_auth_header("riot", self._token))
        ]

        self._ws_client = await websockets.connect(
            uri = f"wss://127.0.0.1:{self._port}",
            ssl = ssl._create_unverified_context(),  # if "sll" is set to False, an HTTP protocol handshake that is not supported by the LCU server will be used, so set "ssl" to unverified ssl.
            additional_headers = headers,
            max_size = 1024 * 1024 * 10  # set the max_size enough big to prevent Error 1009.
        )
        self._ws_alive = True

        self._ws_loop_task = asyncio.create_task(self._ws_loop())  # create ws loop.

        await self._ws_client.send(json.dumps([EventCode.SUBSCRIBE, "OnJsonApiEvent"]))  # subscribe to all json events.
        
        logger.info("Ws is started.")
        return

    async def _ws_loop(self):
        logger.debug("Ws loop is created.")
        try:
            async for msg in self._ws_client:
                if msg == "":
                    logger.info("Got websocket message containing no data.")
                else:
                    data = json.loads(msg)
                    asyncio.create_task(Router._dispatch(data[2])) # dispatch messages with Router.
        except Exception as e:
            logger.warning(f"ws loop error: {e}")
            await Router.fake(None, "Update", "/riotclient/pre-shutdown/begin")
        self._ws_alive = False
        return
    
    async def request(self, method:str, uri:str, **kwargs):
        # Need to check if the http is alive.

        if kwargs.get("data", None):
            kwargs["data"] = json.dumps(kwargs["data"])
        return await self._http_client.request(method, uri, **kwargs)

    async def stop(self):
        await self._stop_http()
        await self._stop_ws()
    
    async def _stop_http(self):
        if self._http_alive:
            await self._http_client.aclose()
            self._http_alive = False

    async def _stop_ws(self):
        if self._ws_alive:
            await self._ws_client.close()
            await self._ws_loop_task
            self._ws_alive = False


class EventCode(IntEnum):
    WELCOME = 0
    PREFIX = 1
    CALL = 2
    CALLRESULT = 3
    CALLERROR = 4
    SUBSCRIBE = 5
    UNSUBSCRIBE = 6
    PUBLISH = 7
    EVENT = 8