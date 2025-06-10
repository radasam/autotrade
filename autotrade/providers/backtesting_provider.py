from abc import ABC, abstractmethod
from typing import Callable
import asyncio
from datetime import datetime, timedelta, timezone
import os
import pandas as pd
import json
import logging
from typing import Dict

pd.options.mode.copy_on_write = True


class BacktestingMarketPrice:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: pd.DataFrame = pd.DataFrame()
        self.current_time: datetime
        self.end_time: datetime

    def load_data(self):
        self.data = pd.read_csv(self.file_path, parse_dates=['time'], index_col=None)
        self.data.sort_values(by='time', inplace=True)
        self.current_time = self.data['time'].min() - timedelta(seconds=1)
        self.end_time = self.data['time'].max()

    def get_next_values(self, time: datetime) -> tuple[str, bool]:
        if time > self.end_time:
            return None, True

        filtered = self.data[(self.data['time'] > self.current_time) & (self.data['time'] <= time)]
        if filtered.empty:
            return None, False
        
        self.current_time = filtered['time'].max()
        
        filtered.sort_values(by='time', inplace=True, ascending=False)
        
        price = filtered['value'].iloc[0]

        dict_out = {"channel": "ticker", "events": [{"tickers": []}]}
        
        dict_out["events"][0]["tickers"].append({"price": str(price)})
        dict_out["timestamp"] = time.isoformat()
        
        return json.dumps(dict_out), False

class BacktestingFileOrders:
    def __init__(self, buys_file: str, sells_file: str):
        self.buys_file = buys_file
        self.sells_file = sells_file
        self.data: pd.DataFrame = pd.DataFrame()
        self.current_time: datetime
    
    def load_data(self):
        buys_data =  pd.read_csv(self.buys_file, parse_dates=['time'], index_col=None)
        buys_data['side'] = 'bid'
        sells_data = pd.read_csv(self.sells_file, parse_dates=['time'], index_col=None)
        sells_data['side'] = 'sell'
        self.data = pd.concat([buys_data, sells_data], ignore_index=True)
        self.data.sort_values(by='time', inplace=True)
        self.current_time = self.data['time'].min() - timedelta(seconds=1)
        self.end_time = self.data['time'].max()

    def get_next_values(self, time: datetime) -> tuple[str, bool]:
        if time > self.end_time:
            return None, True

        filtered = self.data[(self.data['time'] > self.current_time) & (self.data['time'] <= time)]
        if filtered.empty:
            return None, False
        
        self.current_time = filtered['time'].max()
        
        dict_out = {"channel": "l2_data", "events":[{"type": "snapshot"}]}
        filtered = filtered.groupby(['price', 'side']).agg({'volume': 'sum'}).reset_index()
        

        order_updates = []

        for index, row in filtered.iterrows():
            order_updates.append({"side": row['side'], "price_level": str(row['price']), "new_quantity": str(row['volume'])})

        dict_out["events"][0]["updates"] = order_updates
        dict_out["timestamp"] = time.isoformat()
        
        return json.dumps(dict_out), False

class BacktestingFile:
    def __init__(self, file_path: str):
        pass

    @abstractmethod
    def load_data(self):
        pass

    @abstractmethod
    def get_next_values(self, time: datetime) -> str:
        pass

class BacktestingProvider:
    def __init__(self, start_time: datetime, end_time: datetime, interval: timedelta, real_time_factor: float, folder_path: str, on_message: Callable):
        self.start_time = start_time
        self.end_time = end_time
        self.interval = interval
        self.current_time = start_time
        self.folder_path = folder_path
        self.current_time = start_time
        self.data = []
        self.current_files: Dict[str, BacktestingFile] = {}
        self.files: Dict[str, str] = {}
        self.on_message = on_message
        self.real_time_factor = real_time_factor

    def prepare_files(self):
        # Load data from files in the folder_path

        file_prefixes = ['market_price', 'order_buys', 'order_sells']
       
        files = os.listdir(self.folder_path)
        for file in files:
            if not file.endswith('.csv'):
                continue
            metric_type = ""

            for prefix in file_prefixes:
                if file.startswith(prefix):
                    metric_type = prefix
                    break

            if metric_type == "":
                continue

            unix_time = file.split(f"{metric_type}_")[1].split(".")[0]

            if len(unix_time) != 10:
                continue

            end_time = datetime.fromtimestamp(int(unix_time), tz=timezone.utc)

            if end_time < self.start_time:
                continue

            if metric_type not in self.files:
                self.files[metric_type] = {}

            self.files[metric_type][end_time] = os.path.join(self.folder_path, file)

    def get_next_file_for_metric(self, metric_type: str) -> BacktestingFile:
        matched_date = datetime.now(timezone.utc)
        matched_file = ""

        for start_time, file_path in self.files[metric_type].items():
            if start_time > self.current_time:
                if start_time > matched_date:
                    matched_date = start_time
                    matched_file = file_path

        file = BacktestingMarketPrice(matched_file)

        file.load_data()
        self.current_time = file.current_time
        return file
    
    def get_next_event(self):
        for metric_type in ['orders', 'market_price']:
            if metric_type not in self.current_files:
                self.current_files[metric_type] = self.get_next_file_for_metric(metric_type)

            current_file = self.current_files[metric_type]

            data, end = current_file.get_next_values(self.current_time + self.interval)
            while end:
                print("trying to get next file for metric:", metric_type)
                self.current_files[metric_type] = self.get_next_file_for_metric(metric_type)
                if current_file is None:
                    print(f"No more data for {metric_type} at {self.current_time + self.interval}")
                    return None
                
                data, end = current_file.get_next_values(self.current_time + self.interval)

            if data is not None:
                return data
            
        return None
        
            
    async def start(self):
        self.prepare_files()
        await asyncio.sleep(0.1)
        await self._run_interval_loop()

    async def _do_one_iteration(self):
        # print(f"Current time: {self.current_time.isoformat()}")
        event = self.get_next_event()
        if event is not None:
            await self.on_message(event)
            return
        self.current_time = self.current_time + self.interval
        await asyncio.sleep(self.interval.total_seconds())

    async def _run_interval_loop(self):
        while True:
            await self._do_one_iteration()