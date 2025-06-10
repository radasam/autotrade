import asyncio

from autotrade.settings.config import Config

class TestConfig:
    def __init__(self):
        self.config = Config()
        self.original_values = {}
        self.lock = asyncio.Lock()

    def set_value(self, key: str, value):
        config_dict = self.config.model_dump()

        if key in config_dict:
            self.original_values[key] = config_dict[key]

        config_dict[key] = value
        self.config = Config(**config_dict)

    def reset(self):
        config_dict = self.config.model_dump()
        for key, value in self.original_values.items():
            config_dict[key] = value

        self.config = Config(**config_dict)

    async def get_config(self) -> Config:
        """Gets the current configuration in a thread-safe manner."""
        async with self.lock:
            return self.config.model_copy()