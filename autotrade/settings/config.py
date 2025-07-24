import logging
import asyncio 
from abc import ABC, abstractmethod

from pydantic import BaseModel

class Config(BaseModel):
    price_distance_threshold: float = 10000
    order_size_threshold: float = 0.95
    spread_threshold: float = 0.02
    imbalance_threshold: float = 0.3
    min_signals_for_buy_action: int = 5
    min_signals_for_sell_action: int = 3
    take_profit_multiplier: float = 1.0
    take_profit_sensitivity: float = 0.5
    stop_loss_percentage: float = 0.01
    stop_less_offset: float = 0.01
    moving_average_sensitivity: float = 5000
    order_price_multiplier: float = 1
    strategy: str = "moving_average"
    order_type: str = "market"
    min_confidence_for_action: float = 0.5

class ConfigGetter(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def get_config(self) -> Config:
        """Gets the current configuration."""
        pass

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

def set_config(override: ConfigReloader):
    global config
    config = override