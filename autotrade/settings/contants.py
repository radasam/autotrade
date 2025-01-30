import os
import logging

PRODUCT_ENV="PRODUCT"
PRODUCT_ENV_DEFAULT="BTC-USD"

def get_product() -> str:
    return os.getenv(PRODUCT_ENV, PRODUCT_ENV_DEFAULT)