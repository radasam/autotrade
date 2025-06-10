from typing import Protocol

class Provider(Protocol):
    def on_message(self, message: str) -> None:
        """Handle incoming messages."""
        pass

    async def start(self) -> None:
        """Start the provider."""
        pass