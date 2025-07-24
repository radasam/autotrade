from collections import defaultdict, deque
from typing import Optional
from datetime import datetime

from prometheus_client import Gauge

class HistoryStore():
    def __init__(self, max_size: int):
        self.value_history = deque([], maxlen=max_size)
        self.timestamp_history = deque([], maxlen=max_size)

    def append(self, value, timestamp):
        self.value_history.append(value)
        self.timestamp_history.append(timestamp)

    def get_values(self) -> tuple[list[float], list[datetime]]:
        values = list(self.value_history.copy())
        timestamps = list(self.timestamp_history.copy())

        self.value_history.clear()
        self.timestamp_history.clear()

        return (values, timestamps)

class GaugeWrapper():
    def __init__(self, name, documentation: str, labelnames: list[str], store_history: bool, history_size: int = 1000):
        self.gauge = Gauge(name=name, documentation=documentation, labelnames=labelnames)
        self.labelnames = labelnames
        self.store_history = store_history
        self.history: dict[str, HistoryStore] = {}
        self.history_size = history_size
        pass

    def set(self, value: float, labels: list[str], timestamp: Optional[datetime]):
        self.gauge.labels(labels).set(value)
        if self.store_history:
            if timestamp:  
                label_key = labels_to_string(self.labelnames, labels)
                history_store = self.history.get(label_key, None)
                if not history_store:
                    history_store = HistoryStore(self.history_size)
                    self.history[label_key] = history_store
                history_store.append(value, timestamp)

    
    def get_values(self, labels: list[str]) -> tuple[list[float], list[datetime]]:
        label_key = labels_to_string(self.labelnames, labels)
        history_store = self.history.get(label_key, None)
        if history_store:
            return history_store.get_values()
        return ([], [])
    
def labels_to_string(keys,values: list[str]) -> str:
    list_out=[]

    for k, v in zip(keys, values):
        list_out.append(k + ":" + v)

    return ";".join(list_out)