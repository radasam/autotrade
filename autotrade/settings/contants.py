import os
import logging

ORDER_BUY = "BUY"
ORDER_SELL = "SELL"

PRODUCT_ENV="PRODUCT"
PRODUCT_ENV_DEFAULT="BTC-GBP"

def get_product() -> str:
    return os.getenv(PRODUCT_ENV, PRODUCT_ENV_DEFAULT)

EXPORT_BUCKET_ENV="EXPORT_BUCKET"
EXPORT_BUCKET_DEFAULT="autotrade-export-data"

def get_export_bucket() -> str:
    return os.getenv(EXPORT_BUCKET_ENV, EXPORT_BUCKET_DEFAULT)

COINBASE_API_BASE_URL_ENV="COINBASE_API_BASE_URL"
COINBASE_API_BASE_URL="api.coinbase.com"
SANDBOX_API_BASE_URL="api-sandbox.coinbase.com"

def get_coinbase_api_base_url() -> str:
    return os.getenv(COINBASE_API_BASE_URL_ENV, COINBASE_API_BASE_URL)