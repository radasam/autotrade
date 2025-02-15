import asyncio
import threading
import pandas as pd
import dateutil
import datetime
import tempfile
import os

from autotrade.exporter.connectors.connector import Connector

class Exporter:
    def __init__(self, name: str, observations_limit: int, connector: Connector):
        self.name = name
        self.data_frame = pd.DataFrame()
        self.observations = 0
        self.observations_limit = observations_limit
        self.connector = connector
        pass

    def update_dataframe(self, **kwargs):
        value = kwargs["value"]
        update_time = dateutil.parser.parse(kwargs.get("time"))
        row = pd.Series({
            "value": value,
            "time": update_time
        })
        self.data_frame = pd.concat([
                self.data_frame, 
                pd.DataFrame([row], columns=row.index)]
           ).reset_index(drop=True)
        
        self.observations += 1
        if self.observations >= self.observations_limit:
            temp_filename = self.save_to_temporary_file()
            self.data_frame = pd.DataFrame()
            self.observations = 0
            self.connector.export(temp_filename, self.name, f'{self.name}_{int(datetime.datetime.now().timestamp())}')
            os.remove(temp_filename)

    def save_to_temporary_file(self) -> str:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as temp_file:
            temp_filename = temp_file.name  # Get the filename
            self.data_frame.to_csv(temp_file, index=False)  # Write DataFrame to CSV
            temp_file.seek(0)  # Move to the beginning of the file
            print(f"Temporary file created: {temp_filename}")

        return temp_filename
