import os
import logging

PRODUCT_ENV="PRODUCT"
PRODUCT_ENV_DEFAULT="BTC-USD"

EXPORT_BUCKET_ENV="EXPORT_BUCKET"
EXPORT_BUCKET_DEFAULT="autotrade-export-data"

def get_product() -> str:
    return os.getenv(PRODUCT_ENV, PRODUCT_ENV_DEFAULT)

def get_export_bucket() -> str:
    return os.getenv(EXPORT_BUCKET_ENV, EXPORT_BUCKET_DEFAULT)