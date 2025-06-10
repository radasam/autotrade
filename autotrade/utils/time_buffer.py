class TimeBuffer:
    def __init__(self, buffer_seconds: int):
        self.buffer_seconds = buffer_seconds
        self.last_time = None

    def is_time_to_run(self, current_time: float) -> bool:
        if self.last_time is None or (current_time - self.last_time) >= self.buffer_seconds:
            self.last_time = current_time
            return True
        return False