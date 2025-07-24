import asyncio
from typing import Dict
import logging
from datetime import datetime
import threading

from autotrade.events.event_types import EventType, Event

class EventHandler():
    def __init__(self, event_name: EventType):
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

    def trigger(self, value):
        for handler in self.handlers.values():
            asyncio.create_task(handler(value))

class Events():

    def __init__(self):
        self.handlers: Dict[str, EventHandler] = {}
        self.threads = 1

    async def _event_loop(self):
        while True:
            try:
                event = self.queue.get_nowait()  # Receive data from the channel

                if event.event_type not in self.handlers:
                    logging.error(f"[events] tried to call non existant event {event.name}")
                    continue

                handler = self.handlers[event.event_type]
                handler.trigger(event.value)

            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
                continue

    def add_handler(self, id: str, event: EventType, handler):
        if event not in self.handlers:
            self.handlers[event] = EventHandler(event)

        self.handlers[event].add_handler(id, handler)

    def trigger_event(self, event_name: EventType, value):
        event = Event(event_name, value)
        self.queue.put_nowait(event)

    async def start(self):
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=400000, loop=loop)
        consumers = [asyncio.create_task(self._event_loop()) for i in range(self.threads)]
        await asyncio.gather(*consumers)