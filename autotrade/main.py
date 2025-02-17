from autotrade.engine.main import Engine
from autotrade.settings.contants import get_product

import logging
import asyncio


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = Engine(get_product())

    engine.setup()

    asyncio.run(engine.start())