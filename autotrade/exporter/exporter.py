import asyncio
import threading
import pandas as pd
import dateutil
from datetime import datetime, timedelta
import tempfile
import os

from autotrade.exporter.connectors.connector import Connector

class Exporter:
    def __init__(self, name: str, observations_limit: int, time_limit: timedelta, connector: Connector):
        self.name = name
        self.data_frame = pd.DataFrame()
        self.observations = 0
        self.observations_limit = observations_limit
        self.connector = connector
        self.time_limit = time_limit
        self.file_name = ""
        self.start_time = None
        pass

    def update_dataframe(self, **kwargs):
        if "metric_name" in kwargs:
            del kwargs["metric_name"]
        update_time = dateutil.parser.parse(kwargs.get("time"))

        if self.file_name == "":
            self.file_name = f"{self.name}_{int(update_time.timestamp())}"

        if self.start_time is None:
            self.start_time = datetime.now()

        row = pd.Series({**kwargs, "time": update_time})
        self.data_frame = pd.concat([
                self.data_frame, 
                pd.DataFrame([row], columns=row.index)]
           ).reset_index(drop=True)
        
        self.observations += 1

        if datetime.now() - self.start_time > self.time_limit:
            self.export()
            return

        if self.observations >= self.observations_limit:
            self.export()
            return

    def export(self):
        temp_filename = self.save_to_temporary_file()
        self.data_frame = pd.DataFrame()
        self.observations = 0
        self.connector.export(temp_filename, self.name, self.file_name)
        os.remove(temp_filename)
        self.file_name = ""
        self.start_time = datetime.now()

    def save_to_temporary_file(self) -> str:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as temp_file:
            temp_filename = temp_file.name  # Get the filename
            self.data_frame.to_csv(temp_file, index=False)  # Write DataFrame to CSV
            temp_file.seek(0)  # Move to the beginning of the file
            print(f"Temporary file created: {temp_filename}")

        return temp_filename
