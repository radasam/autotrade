from datetime import datetime, timedelta, timezone
import json
import pytest

from autotrade.providers.backtesting_provider import BacktestingProvider, BacktestingFileOrders, BacktestingMarketPrice

# def test_prepare_files():
#     # Test the prepare_files method of BacktestingProvider
#     start_time = datetime(2025, 1, 1)
#     end_time = datetime(2025, 12, 31)
#     folder_path = "./exported_data"
    
#     provider = BacktestingProvider(start_time, end_time, timedelta(seconds=1), folder_path)
#     provider.prepare_files()
    
#     assert len(provider.files) > 0
#     assert 'market_price' in provider.files
#     assert 'order_buys' in provider.files
#     assert 'order_sells' in provider.files

def test_backtesting_orders():
    fo = BacktestingFileOrders("/Users/samradage/repos/autotrade/exported_data/order_buys_1746978037.csv", "buy")
    fo.load_data()
    json_string, is_end =  fo.get_next_values(datetime.fromisoformat("2025-05-11 15:29:00+00:00"))

    dict_data = json.loads(json_string)

    assert dict_data["channel"] == "l2_data"
    assert dict_data["events"][0]["type"] == "snapshot"

    assert len(dict_data["events"][0]["updates"]) == 1036
    assert dict_data["events"][0]["updates"][0]["side"] == "buy"
    assert dict_data["events"][0]["updates"][0]["price_level"] == '16200.0'
    assert dict_data["events"][0]["updates"][0]["new_quantity"] == '0.005'

def test_backtesting_price():
    fo = BacktestingMarketPrice("/Users/samradage/repos/autotrade/exported_data/market_price_1746986012.csv")
    fo.load_data()
    json_string, is_end = fo.get_next_values(datetime.fromisoformat("2025-05-11 16:00:00+00:00"))

    dict_data = json.loads(json_string)

    assert dict_data["channel"] == "ticker"

    assert len(dict_data["events"][0]["tickers"]) == 1

@pytest.mark.asyncio
async def test_backtesting_provider_one_iteration():
    start_time = datetime(2025, 5, 11, 15, 28, 59, tzinfo=timezone.utc)
    end_time = datetime(2025, 5, 12, 0, 0, 0, tzinfo=timezone.utc)
    folder_path = "./test_exported_data"

    expected_msg = ""

    def assert_message(msg: str):
        nonlocal expected_msg
        print(msg)
        expected_msg = msg

    provider = BacktestingProvider(start_time, end_time, timedelta(seconds=1), folder_path, assert_message)
    provider.prepare_files()
    
    await provider._do_one_iteration()

    
    assert expected_msg == '{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "78451.41", "new_quantity": "0.01149928"}]}], "timestamp": "2025-05-11T15:28:59.832710+00:00"}'

@pytest.mark.asyncio
async def test_backtesting_provider_two_iterations():
    start_time = datetime(2025, 5, 11, 15, 28, 59, tzinfo=timezone.utc)
    end_time = datetime(2025, 5, 12, 0, 0, 0, tzinfo=timezone.utc)
    folder_path = "./test_exported_data"

    expected_msgs = []

    def assert_message(msg: str):
        nonlocal expected_msgs
        expected_msgs.append(msg)

    provider = BacktestingProvider(start_time, end_time, timedelta(seconds=1), folder_path, assert_message)
    provider.prepare_files()
    
    await provider._do_one_iteration()

    await provider._do_one_iteration()
    
    assert expected_msgs == ['{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "78451.41", "new_quantity": "0.01149928"}]}], "timestamp": "2025-05-11T15:28:59.832710+00:00"}', '{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "78451.4", "new_quantity": "0.01916547"}]}], "timestamp": "2025-05-11T15:29:00.832710+00:00"}']

@pytest.mark.asyncio
async def test_backtesting_provider_end_of_file():
    start_time = datetime(2025, 5, 11, 15, 28, 59, tzinfo=timezone.utc)
    end_time = datetime(2025, 5, 12, 0, 0, 0, tzinfo=timezone.utc)
    folder_path = "./test_exported_data"

    expected_msgs = []

    def assert_message(msg: str):
        nonlocal expected_msgs
        expected_msgs.append(msg)

    provider = BacktestingProvider(start_time, end_time, timedelta(seconds=1), folder_path, assert_message)
    provider.prepare_files()
    
    await provider._do_one_iteration()

    await provider._do_one_iteration()

    await provider._do_one_iteration()
    
    assert expected_msgs == ['{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "78451.41", "new_quantity": "0.01149928"}]}], "timestamp": "2025-05-11T15:28:59.832710+00:00"}', '{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "78451.4", "new_quantity": "0.01916547"}]}], "timestamp": "2025-05-11T15:29:00.832710+00:00"}', '{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "500.41", "new_quantity": "0.025"}]}], "timestamp": "2025-05-11T15:29:05.832710+00:00"}']

@pytest.mark.asyncio
async def test_backtesting_provider_end_all():
    start_time = datetime(2025, 5, 11, 15, 28, 59, tzinfo=timezone.utc)
    end_time = datetime(2025, 5, 12, 0, 0, 0, tzinfo=timezone.utc)
    folder_path = "./test_exported_data"

    expected_msgs = []

    def assert_message(msg: str):
        nonlocal expected_msgs
        expected_msgs.append(msg)

    provider = BacktestingProvider(start_time, end_time, timedelta(seconds=1), folder_path, assert_message)
    provider.prepare_files()
    
    await provider._do_one_iteration()

    await provider._do_one_iteration()

    await provider._do_one_iteration()

    await provider._do_one_iteration()
    
    assert expected_msgs == ['{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "78451.41", "new_quantity": "0.01149928"}]}], "timestamp": "2025-05-11T15:28:59.832710+00:00"}', '{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "78451.4", "new_quantity": "0.01916547"}]}], "timestamp": "2025-05-11T15:29:00.832710+00:00"}', '{"channel": "l2_data", "events": [{"type": "snapshot", "updates": [{"side": "buys", "price_level": "500.41", "new_quantity": "0.025"}]}], "timestamp": "2025-05-11T15:29:05.832710+00:00"}']