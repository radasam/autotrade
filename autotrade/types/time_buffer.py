import time
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Union
from collections.abc import Iterator

class TimeBuffer:
    """High-performance circular buffer with item aging."""
    
    def __init__(self, capacity: int, max_age: float = float(60)):
        """
        Initialize time buffer.
        
        Args:
            capacity: Maximum number of items to store
            max_age: Maximum age of items in seconds (default: 60s)
        """
        self.capacity = capacity
        self.max_age: timedelta = timedelta(seconds=max_age)
        self.buffer: list[float] = [None] * capacity
        self.timestamps: list[datetime] = [None] * capacity
        self.head = 0
        self.tail = 0
        self.size = 0
        self.total = 0
    
    def push(self, item: float, dt: Optional[datetime]) -> None:
        """Add item to buffer. O(1) amortized."""
        if not dt:
            dt = datetime.now(tz=timezone.utc)
        
        # Store item and timestamp
        self.buffer[self.tail] = item
        self.timestamps[self.tail] = dt
        
        # Update tail pointer
        self.tail = (self.tail + 1) % self.capacity
        
        # If buffer is full, advance head (overwrite oldest)
        if self.size == self.capacity:
            self.total -= self.buffer[self.head]
            self.head = (self.head + 1) % self.capacity
        else:
            self.size += 1
            
        self.total += item
        
        # Clean expired items if needed
        self._clean_expired(dt, "push")
    
    def get_all(self) -> List[float]:
        """Get all valid (non-expired) items. O(n) where n = valid items."""
        now = datetime.now(tz=timezone.utc)
        self._clean_expired(now, "get_all")
        
        result = []
        for i in range(self.size):
            idx = (self.head + i) % self.capacity
            if now - self.timestamps[idx] <= self.max_age:
                result.append(self.buffer[idx])
        return result
    
    def peek(self) -> Optional[Any]:
        """Get most recent item (if not expired). O(1)."""
        if self.size == 0:
            return None
        
        now = datetime.now(tz=timezone.utc)
        last_idx = (self.tail - 1) % self.capacity
        
        if now - self.timestamps[last_idx] <= self.max_age:
            return self.buffer[last_idx]
        return None
    
    def peek_oldest(self) -> Optional[Any]:
        """Get oldest item (if not expired). O(1) amortized."""
        if self.size == 0:
            return None
        
        now = datetime.now(tz=timezone.utc)
        self._clean_expired(now, "peek_oldest")
        
        if self.size > 0 and now - self.timestamps[self.head] <= self.max_age:
            return self.buffer[self.head]
        return None
    
    def pop(self) -> Optional[Any]:
        """Remove and return oldest item. O(1)."""
        if self.size == 0:
            return None
        
        item = self.buffer[self.head]
        self.buffer[self.head] = None  # Help GC
        self.timestamps[self.head] = None
        
        self.head = (self.head + 1) % self.capacity
        self.size -= 1
        
        return item
    
    def _clean_expired(self, now: datetime, caller: str) -> None:
        """Clean expired items from head. O(k) where k = expired items."""
        while self.size > 0 and now - self.timestamps[self.head] > self.max_age:
            self.total -= self.buffer[self.head]
            self.buffer[self.head] = None  # Help GC
            self.timestamps[self.head] = None
            self.head = (self.head + 1) % self.capacity
            self.size -= 1
    
    def cleanup(self) -> None:
        """Force cleanup of all expired items."""
        self._clean_expired(datetime.now(tz=timezone.utc), "cleanup")
    
    def get_size(self) -> int:
        """Get current size (excludes expired items). O(k) where k = expired items."""
        self._clean_expired(datetime.now(tz=timezone.utc), "get_size")
        return self.size
    
    def is_empty(self) -> bool:
        """Check if buffer is empty. O(k) where k = expired items."""
        self._clean_expired(datetime.now(tz=timezone.utc), "is_empty")
        return self.size == 0
    
    def is_full(self) -> bool:
        """Check if buffer is full. O(k) where k = expired items."""
        self._clean_expired(datetime.now(tz=timezone.utc), "is_full")
        return self.size == self.capacity
    
    def clear(self) -> None:
        """Clear all items. O(1)."""
        self.buffer = [None] * self.capacity
        self.timestamps = [None] * self.capacity
        self.head = 0
        self.tail = 0
        self.size = 0
   
    def get_average(self, dt: Optional[datetime]) -> float:
        """Get the average of all items in the buffer"""
        if not dt:
            dt = datetime.now(tz=timezone.utc)

        self._clean_expired(dt, "get_average")
        return self.total/self.size


    def __len__(self) -> int:
        """Get current size."""
        return self.get_size()
    
    def __bool__(self) -> bool:
        """Check if buffer is not empty."""
        return not self.is_empty()
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate over valid items (oldest to newest)."""
        now = datetime.now(tz=timezone.utc)
        self._clean_expired(now, "__iter__")
        
        for i in range(self.size):
            idx = (self.head + i) % self.capacity
            if now - self.timestamps[idx] <= self.max_age:
                yield self.buffer[idx]
    
    def __repr__(self) -> str:
        """String representation."""
        return f"CircularBuffer(capacity={self.capacity}, max_age={self.max_age}, size={self.get_size()})"
