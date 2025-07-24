from typing import Dict, List, Optional, Any, Tuple
from prometheus_client import Gauge, CollectorRegistry
import threading
import time
from datetime import datetime
from collections import defaultdict, deque
import copy

class MemoryGauge:
    """
    A Prometheus gauge that stores all values in memory for later retrieval.
    
    This class wraps a standard Prometheus Gauge and maintains a history of all
    values that have been set, including timestamps and labels.
    """
    
    def __init__(self, name: str, description: str, labelnames: Optional[List[str]] = None, 
                 registry: Optional[CollectorRegistry] = None, max_history: Optional[int] = None,
                 store_history: bool = True):
        """
        Initialize the memory gauge.
        
        Args:
            name: The name of the gauge metric
            description: A description of what the gauge measures
            labels: Optional list of label names for the gauge
            registry: Optional custom registry. If None, uses the default registry.
            max_history: Maximum number of values to store per label combination (None = unlimited)
            store_history: Whether to store values in memory (default: True)
        """
        self.name = name
        self.description = description
        self.label_names = labelnames or []
        self.max_history = max_history
        self.store_history = store_history
        self._lock = threading.Lock()
        
        # Create the actual Prometheus gauge
        self._gauge = Gauge(
            name=name,
            documentation=description,
            labelnames=self.label_names,
            registry=registry
        )
        
        # Storage for historical values (only if store_history is True)
        if self.store_history:
            # Structure: {label_key: deque[(timestamp, value)]}
            self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
            
            # Current values for quick access
            # Structure: {label_key: value}
            self._current_values: Dict[str, float] = {}
        else:
            self._history = None
            self._current_values = None
    
    def _get_label_key(self, labels: Optional[Dict[str, str]] = None) -> str:
        """
        Generate a consistent key for label combinations.
        
        Args:
            labels: Dictionary of label key-value pairs
            
        Returns:
            str: A consistent string key for the label combination
        """
        if not labels:
            return ""
        
        # Sort labels by key to ensure consistent ordering
        sorted_labels = sorted(labels.items())
        return "|".join(f"{k}={v}" for k, v in sorted_labels)
    
    def _prepare_lables(self, labeltuple: Optional[Tuple[str]], labelDict: Optional[Dict[str, str]]) -> Dict[str, str]:
        dict_out = {}

        labeltuple = [i for i in labeltuple if i != ""]

        if labeltuple:
            if len(labeltuple) != len(self.label_names):
                return dict_out

            for i in range(len(self.label_names)):
                dict_out[self.label_names[i]] = labeltuple[i]

            return dict_out
        
        return labelDict
    
    def _validate_labels(self, labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Validate that provided labels match the gauge's label names.
        
        Args:
            labels: Dictionary of label key-value pairs
            
        Returns:
            bool: True if labels are valid, False otherwise
        """
        if not labels and not self.label_names:
            return True
        
        if not labels and self.label_names:
            return False
        
        if labels and not self.label_names:
            return False
        
        if set(labels.keys()) != set(self.label_names):
            return False
        
        return True
    
    def set(self, value: float, labeltuple: Optional[Tuple[str]], labelDict: Optional[Dict[str, str]] = None) -> bool:
        """
        Set the gauge value and store it in memory if enabled.
        
        Args:
            value: The value to set
            labels: Optional dictionary of label key-value pairs
            
        Returns:
            bool: True if value was set successfully, False otherwise
        """


        labels = self._prepare_lables(labeltuple, labelDict)

        if not self._validate_labels(labels):
            return False
        
        with self._lock:
            try:
                # Set the Prometheus gauge value
                if labels:
                    self._gauge.labels(**labels).set(value)
                else:
                    self._gauge.set(value)
                
                # Store in memory only if history storage is enabled
                if self.store_history:
                    label_key = self._get_label_key(labels)
                    timestamp = time.time()
                    self._history[label_key].append((timestamp, value))
                    self._current_values[label_key] = value
                return True
            except Exception:
                return False
    
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Increment the gauge value by a specified amount.
        
        Args:
            amount: The amount to increment by (default: 1.0)
            labels: Optional dictionary of label key-value pairs
            
        Returns:
            bool: True if value was incremented successfully, False otherwise
        """
        if not self._validate_labels(labels):
            return False
        
        with self._lock:
            try:
                # Increment the Prometheus gauge
                if labels:
                    self._gauge.labels(**labels).inc(amount)
                else:
                    self._gauge.inc(amount)
                
                # Update memory storage only if history storage is enabled
                if self.store_history:
                    label_key = self._get_label_key(labels)
                    current_value = self._current_values.get(label_key, 0.0)
                    new_value = current_value + amount
                    
                    timestamp = time.time()
                    self._history[label_key].append((timestamp, new_value))
                    self._current_values[label_key] = new_value
                
                return True
            except Exception:
                return False
    
    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Decrement the gauge value by a specified amount.
        
        Args:
            amount: The amount to decrement by (default: 1.0)
            labels: Optional dictionary of label key-value pairs
            
        Returns:
            bool: True if value was decremented successfully, False otherwise
        """
        return self.inc(-amount, labels)
    
    def get_current_value(self, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """
        Get the current value of the gauge.
        
        Args:
            labels: Optional dictionary of label key-value pairs
            
        Returns:
            Optional[float]: The current value or None if not set/history not stored
        """
        if not self.store_history:
            return None
        
        if not self._validate_labels(labels):
            return None
        
        with self._lock:
            label_key = self._get_label_key(labels)
            return self._current_values.get(label_key)
    
    def get_history(self, labels: Optional[Dict[str, str]] = None) -> List[Tuple[float, float]]:
        """
        Get the complete history of values for a label combination.
        
        Args:
            labels: Optional dictionary of label key-value pairs
            
        Returns:
            List[Tuple[float, float]]: List of (timestamp, value) tuples, empty if history not stored
        """
        if not self.store_history:
            return []
        
        if not self._validate_labels(labels):
            return []
        
        with self._lock:
            label_key = self._get_label_key(labels)
            values = list(self._history.get(label_key, []))
            if self._history.get(label_key):
                self._history.get(label_key).clear()
            return values
    
    def get_all_histories(self) -> Dict[str, List[Tuple[float, float]]]:
        """
        Get the complete history for all label combinations.
        
        Returns:
            Dict[str, List[Tuple[float, float]]]: Dictionary mapping label keys to history lists, empty if history not stored
        """
        if not self.store_history:
            return {}
        
        with self._lock:
            return {
                label_key: list(history) 
                for label_key, history in self._history.items()
            }
    
    def get_all_current_values(self) -> Dict[str, float]:
        """
        Get all current values for all label combinations.
        
        Returns:
            Dict[str, float]: Dictionary mapping label keys to current values, empty if history not stored
        """
        if not self.store_history:
            return {}
        
        with self._lock:
            return copy.deepcopy(self._current_values)
    
    def get_history_as_arrays(self, labels: Optional[Dict[str, str]] = None) -> Tuple[List[float], List[float]]:
        """
        Get the history as separate timestamp and value arrays.
        
        Args:
            labels: Optional dictionary of label key-value pairs
            
        Returns:
            Tuple[List[float], List[float]]: (timestamps, values) arrays
        """
        history = self.get_history(labels)
        if not history:
            return [], []
        
        timestamps, values = zip(*history)
        return list(timestamps), list(values)
    
    def get_history_since(self, since_timestamp: float, labels: Optional[Dict[str, str]] = None) -> List[Tuple[float, float]]:
        """
        Get history entries since a specific timestamp.
        
        Args:
            since_timestamp: Unix timestamp to filter from
            labels: Optional dictionary of label key-value pairs
            
        Returns:
            List[Tuple[float, float]]: List of (timestamp, value) tuples since the given time
        """
        history = self.get_history(labels)
        return [(ts, val) for ts, val in history if ts >= since_timestamp]
    
    def get_statistics(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Get basic statistics for the gauge history.
        
        Args:
            labels: Optional dictionary of label key-value pairs
            
        Returns:
            Dict[str, float]: Dictionary with min, max, avg, count statistics
        """
        history = self.get_history(labels)
        if not history:
            return {}
        
        values = [val for _, val in history]
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values),
            'first_timestamp': history[0][0],
            'last_timestamp': history[-1][0]
        }
    
    def clear_history(self, labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Clear the history for a specific label combination or all combinations.
        
        Args:
            labels: Optional dictionary of label key-value pairs. If None, clears all history.
            
        Returns:
            bool: True if history was cleared successfully or if history storage is disabled
        """
        if not self.store_history:
            return True
        
        with self._lock:
            try:
                if labels is None:
                    # Clear all history
                    self._history.clear()
                    self._current_values.clear()
                else:
                    if not self._validate_labels(labels):
                        return False
                    
                    label_key = self._get_label_key(labels)
                    if label_key in self._history:
                        del self._history[label_key]
                    if label_key in self._current_values:
                        del self._current_values[label_key]
                
                return True
            except Exception:
                return False
    
    def get_label_combinations(self) -> List[Dict[str, str]]:
        """
        Get all label combinations that have been used.
        
        Returns:
            List[Dict[str, str]]: List of label dictionaries, empty if history not stored
        """
        if not self.store_history:
            return []
        
        with self._lock:
            combinations = []
            for label_key in self._history.keys():
                if label_key == "":
                    combinations.append({})
                else:
                    label_dict = {}
                    for pair in label_key.split("|"):
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            label_dict[key] = value
                    combinations.append(label_dict)
            return combinations
        
    def labels(self, *labelvalues: Any, **labelkwargs: Any) :
        return MemoryGaugeSetter(self, labelvalues, labelkwargs)
    
    @property
    def prometheus_gauge(self) -> Gauge:
        """
        Get the underlying Prometheus gauge object.
        
        Returns:
            Gauge: The Prometheus gauge instance
        """
        return self._gauge


class MemoryGaugeSetter:
    def __init__(self, memory_guage: MemoryGauge, *labelvalues: Any):
        self.memory_guage = memory_guage
        self.labelValues = labelvalues[0]
        self.labelkwargs = labelvalues[1]
        pass

    def set(self, value: float):
       return self.memory_guage.set(value, self.labelValues, self.labelkwargs)