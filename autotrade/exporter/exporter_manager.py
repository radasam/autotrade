import asyncio
import threading
from typing import Dict

from autotrade.exporter.exporter import Exporter

class ExporterManager:
    def __init__(self, enabled: bool = True):
        self.exporters : Dict[str, Exporter] = {}
        self.threads = 1
        self.started = False
        self.enabled = enabled
        pass

    def add_observation(self, **kwargs):
        if not self.enabled:
            return
        if not self.started:
            return
        try:
            self.queue.put_nowait(kwargs)
        except asyncio.QueueFull:
            print(f"{self.name} queue full")
            pass

    async def _handle_update(self):
        while True:
            try:
                kwargs = self.queue.get_nowait()
                self.update_exporter(**kwargs)
                self.queue.task_done()

            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
                continue


    def update_exporter(self, **kwargs):
        metric_name = kwargs.get("metric_name")
        if self.exporters.get(metric_name) is not None:
            self.exporters[metric_name].update_dataframe(**kwargs)
            return
        
        print(f"Exporter for metric {metric_name} not found")

    def add_exporter(self, metric_name: str, exporter: Exporter):
        self.exporters[metric_name] = exporter
        pass

    async def start(self):
        if not self.enabled:
            return
        self.started = True
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=400000, loop=loop)
        consumers = [asyncio.create_task(self._handle_update()) for i in range(self.threads)]
        await asyncio.gather(*consumers)



exporter_manager = ExporterManager(False)