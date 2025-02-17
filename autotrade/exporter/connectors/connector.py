from abc import ABC, abstractmethod

class Connector(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def export(self, file_path: str, exported_metric: str, output_name: str):
        pass