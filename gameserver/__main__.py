import asyncio
import os
import sys

from common import GAMESERVER_ADDR
from common.res import load_res
from common.util import Log

from .client import handle_client


class Tee:
    def __init__(self, filename: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.file = open(filename, "a", encoding="utf-8")
        self.stdout = sys.__stdout__

    def write(self, data: str):
        self.stdout.write(data)
        self.file.write(data)
        self.file.flush()

    def flush(self):
        self.stdout.flush()
        self.file.flush()

    def isatty(self):
        return False

    def fileno(self):
        return self.stdout.fileno() if hasattr(self.stdout, "fileno") else 1


sys.stdout = Tee("logs/gameserver.log")
sys.stderr = sys.stdout


async def start_server() -> None:
    await load_res()
    Log.info("res loaded.")
    host, port = GAMESERVER_ADDR
    server = await asyncio.start_server(handle_client, host, port)
    Log.info(f"gameserver listening on {host}:{port}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        pass
