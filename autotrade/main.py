from autotrade.engine.main import Engine
from autotrade.settings.contants import get_product

import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = Engine(get_product())

    engine.start()