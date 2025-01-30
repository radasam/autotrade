from abc import ABC, abstractmethod

class MetricValue(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def update(self, queue_depth: int, **kwargs):
        pass
    
    @abstractmethod
    def get_value(self):
        pass