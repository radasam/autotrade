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
        self.start_time: datetime

    def load_data(self):
        self.data = pd.read_csv(self.file_path, parse_dates=['time'], index_col=None)
        self.data.sort_values(by='time', inplace=True)
        self.start_time = self.data['time'].min()
        self.current_time = self.data['time'].min()
        self.end_time = self.data['time'].max()
        print("loaded file", self.file_path, "start", self.start_time, "end", self.end_time, "current", self.current_time)

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
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: pd.DataFrame = pd.DataFrame()
        self.current_time: datetime
        self.start_time: datetime
    
    def load_data(self):
        self.data =  pd.read_csv(self.file_path, parse_dates=['time'], index_col=None)
        self.data.sort_values(by='time', inplace=True)
        self.start_time = self.data['time'].min()
        self.current_time = self.data['time'].min()
        self.end_time = self.data['time'].max()
        print("loaded file", self.file_path, "start", self.start_time, "end", self.end_time, "current", self.current_time)

    def get_next_values(self, time: datetime) -> tuple[str, bool]:
        if time > self.end_time:
            return None, True
        
        filtered = self.data[(self.data['time'] > self.current_time) & (self.data['time'] <= time)]
        if filtered.empty:
            self.current_time = time
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
    def __init__(self, file_path: str, current_time: datetime):
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
        self.data = []
        self.current_files: Dict[str, BacktestingFile] = {}
        self.files: Dict[str, str] = {}
        self.on_message = on_message
        self.real_time_factor = real_time_factor

    def prepare_files(self):
        # Load data from files in the folder_path

        file_prefixes = ['market_price', 'orders']
       
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

            start_time = datetime.fromtimestamp(int(unix_time), tz=timezone.utc)

            if start_time < self.start_time:
                continue

            filepath = os.path.join(self.folder_path, file)

            if metric_type not in self.files:
                self.files[metric_type] = {}

            self.files[metric_type][start_time] = filepath


    def get_next_file_for_metric(self, metric_type: str) -> BacktestingFile:
        matched_date = None
        matched_file = ""

        for start_time, file_path in self.files[metric_type].items():
            if start_time > self.current_time:
                if not matched_date or start_time < matched_date:
                    matched_date = start_time
                    matched_file = file_path
        
        if matched_file == "":
            return None
        
        if metric_type == 'market_price':
            file = BacktestingMarketPrice(matched_file)
        else:
            file = BacktestingFileOrders(matched_file)

        file.load_data()
        return file
    
    def initialise_files(self):
        min_start_time = None

        for metric_type in ['market_price', 'orders']:
            if metric_type not in self.current_files:
                current_file = self.get_next_file_for_metric(metric_type)
                if not min_start_time or min_start_time < current_file.start_time:
                    min_start_time = current_file.start_time - self.interval
                self.current_files[metric_type] = current_file
                
        logging.info("setting start time to " + str(min_start_time))
        self.current_time = min_start_time
    
    def get_next_event(self):
        for metric_type in ['market_price', 'orders']:
            if metric_type not in self.current_files:
                current_file = self.get_next_file_for_metric(metric_type)
                if not current_file:
                    print(f"No more data for {metric_type} at {self.current_time + self.interval}")
                    return None
                self.current_files[metric_type] = current_file
            data, end = self.current_files[metric_type].get_next_values(self.current_time + self.interval)
            while end:
                print("trying to get next file for metric:", metric_type)
                current_file = self.get_next_file_for_metric(metric_type)
                if not current_file:
                    print(f"No more data for {metric_type} at {self.current_time + self.interval}")
                    return None
                
                self.current_files[metric_type] = current_file
                
                data, end = self.current_files[metric_type].get_next_values(self.current_time + self.interval)

            if data is not None:
                return data
            
        return None
        
            
    async def start(self):
        self.prepare_files()
        self.initialise_files()
        await asyncio.sleep(0.1)
        await self._run_interval_loop()

    async def _do_one_iteration(self):
        # print(f"Current time: {self.current_time.isoformat()}")
        event = self.get_next_event()
        if event is not None:
            self.on_message(event)
            return
        self.current_time = self.current_time + self.interval
        await asyncio.sleep(self.interval.total_seconds()/self.real_time_factor)

    async def _run_interval_loop(self):
        while True:
            await self._do_one_iteration()


def get_start_time_for_file(filepath: str):
    file = BacktestingMarketPrice(filepath)
    file.load_data()
    return file.current_time