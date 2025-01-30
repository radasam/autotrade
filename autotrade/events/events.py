import asyncio
from typing import Dict
import logging
import threading

class Event():
    def __init__(self, event_name: str):
        self.event_name = event_name
        self.handlers = {}
        pass

    def add_handler(self, id: str, handler: str):
        if id not in self.handlers:
            logging.info(f"[events] adding event handler {self.event_name} {id}")
            self.handlers[id] = handler

    def remove_handler(self, id: str):
        if id not in self.handlers:
            logging.error(f"[events] tried to delete non existant handler {self.event_name} {id}")
            return
        
        logging.info(f"[events] removing event handler {self.event_name} {id}")
        del self.handlers[id]

    def trigger(self):
        for handler in self.handlers.values():
            handler()

class Events():

    def __init__(self):
        self.handlers: Dict[str, Event] = {}

    async def _event_loop(self):
        while True:
            try:
                event_name = self.metrics_channel.get_nowait()  # Receive data from the channel

                if event_name not in self.handlers:
                    logging.error(f"[events] tried to call non existant event {event_name}")
                    continue

                event = self.handlers[event_name]
                event.trigger()

            except asyncio.QueueEmpty:
                continue

    def add_handler(self, id: str, event: str, handler):
        if event not in self.handlers:
            self.handlers[event] = Event(event)

        self.handlers[event].add_handler(id, handler)

    def trigger_event(self, event: str):
        self.metrics_channel.put_nowait(event)

    async def _start(self):
        loop = asyncio.get_event_loop()
        self.metrics_channel = asyncio.Queue(maxsize=10000, loop=loop)
        await self._event_loop()

    def start(self):
        self.thread = threading.Thread(target=asyncio.run, args=(self._start(),))
        self.thread.start()