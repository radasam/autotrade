import logging
import asyncio 

from pydantic import BaseModel

class Config(BaseModel):
    order_cutoff_percentile: float = 0.1


class ConfigReloader():
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.config = Config()
        self.lock = asyncio.Lock()
        self.interval = 300
        self.threads = 1
        pass

    async def get_config(self) -> Config:
        """Gets the current configuration in a thread-safe manner."""
        async with self.lock:
            return self.config.model_copy()


    async def load_config_from_file(self):
        try:
            with open(self.filepath, 'r') as f:
                new_config = Config.model_validate_json(f.read())
                if new_config != self.config:
                    async with self.lock:
                        self.config = new_config
                        logging.info(f"Config reloaded: {self.config}")
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            

    async def _reload_periodically(self):
        """Reloads the config periodically."""
        while True:
            await self.load_config_from_file()
            await asyncio.sleep(self.interval)

    async def _start(self):
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=100000, loop=loop)
        await self._reload_periodically()

    async def start(self):
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=400000, loop=loop)
        consumers = [asyncio.create_task(self._reload_periodically()) for i in range(self.threads)]
        await asyncio.gather(*consumers)


config = ConfigReloader("./test_config.json")