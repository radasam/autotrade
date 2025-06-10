from autotrade.events.event_types import EventType, Event

class MockEvents():
    """
    Mock class for Events to be used in tests.
    This class is used to simulate the behavior of the Events class
    """
    def __init__(self):
        self.queued_events: dict[EventType, list[Event]] = {}

    def trigger_event(self, event_name: EventType, value):
        event = Event(event_name, value)
        if event_name not in self.queued_events:
            self.queued_events[event_name] = []
        self.queued_events[event_name].append(event)