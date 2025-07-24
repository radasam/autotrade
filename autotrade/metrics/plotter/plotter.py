import asyncio
import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
from collections import deque
import numpy as np
from typing import Optional, Callable, Any, Protocol
import threading
import queue


class DataInterface(Protocol):
    """Protocol defining the interface for data sources"""
    def get_all_current_values(self, product: str) -> np.ndarray:
        """Returns current array of values to plot"""
        ...

class PlotterLine:
    def __init__(
        self,
        product: str,
        data_interface: Callable[[str], list[tuple[float, float]]],
        color: str,
        max_points: int = 10000,
    ):
        self.product = product
        self.data_interface = data_interface
        self.color = color if color in ['b','g','r', 'c', 'm', 'y'] else 'b'
        
        # Data storage
        self.data_history = deque(maxlen=max_points)
        self.time_history = deque(maxlen=max_points)
        self.start_time = None
        self._data_queue = queue.Queue()
        

    def fetch_data(self):
        # Fetch data from interface
        data = self.data_interface([self.product])
        
        if data is not None:
            # Put data in queue for the animation to pick up
            try:
                self._data_queue.put_nowait(data)
            except queue.Full:
                # Remove old data if queue is full
                try:
                    self._data_queue.get_nowait()
                    self._data_queue.put_nowait(data)
                except queue.Empty:
                    pass

    def update_history(self):
        try:
            latest_data = self._data_queue.get_nowait()
            if not latest_data:
                return
            if len(latest_data) == 0:
                return
            self.data_history.extend([i for i in latest_data[0]])
            self.time_history.extend([i for i in latest_data[1]])
        except queue.Empty:
            return

    
class Plotter:
    def __init__(
        self,
        product: str,
        update_interval: float = 0.1,
        max_points: int = 10000,
        figsize: tuple = (10, 6),
        title: str = "Live Data",
        ylabel: str = "Value",
        xlabel: str = "Time"
    ):
        self.product = product
        self.update_interval = update_interval
        self.max_points = max_points
        
        # Data storage
        self.start_time = None
        
        # Plot setup
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_title(title)
        self.ax.set_ylabel(ylabel)
        self.ax.set_xlabel(xlabel)
        self.ax.grid(True, alpha=0.3)
        self.fig.autofmt_xdate()  # Rotates and aligns dates
        self.ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(self.ax.xaxis.get_major_locator()))
        
        # Line objects for plotting
        self.lines = []
        
        # Control flags
        self.is_running = False
        self.is_paused = False
        
        # Animation object
        self.animation = None
        
        # Background async task
        self._data_task = None

        # Store plot style
        self.plot_style = {
            'title': title,
            'xlabel': xlabel,
            'ylabel': ylabel
        }

        self.plots:list[PlotterLine] = []

    def add_plot(self, data_interface: DataInterface, color: str):
        self.plots.append(PlotterLine(self.product, data_interface, max_points=self.max_points, color=color))
        

    async def start_async(self):
        """Start the async data fetching (call this from your async context)"""
        if self._data_task is not None:
            return
            
        self.is_running = True
        self.is_paused = False
        self.start_time = asyncio.get_event_loop().time()
        
        # Start the background data fetching task
        self._data_task = asyncio.create_task(self._data_fetch_loop())

    def start_plot(self):
        """Start the matplotlib animation (call this from main thread)"""
        if self.animation is not None:
            return
            
        # Create animation - this must run on main thread
        self.animation = animation.FuncAnimation(
            self.fig, 
            self._update_plots, 
            interval=int(self.update_interval * 1000),  # Convert to milliseconds
            blit=False,
            cache_frame_data=False
        )
        
        plt.show()

    def _update_plots(self, frame):
        """Update the matplotlib plot with new data (called by animation)"""
        # Get all available data from queue
        for plot in self.plots:
            plot.update_history()
            
        try:

            self.ax.clear()
            for plot in self.plots:
                self.ax.plot(plot.time_history, plot.data_history, plot.color + "-", linewidth=2)
            
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel(self.plot_style['ylabel'])
            self.ax.set_title(self.plot_style['title'])
            self.ax.grid(True, alpha=0.3)
            self.fig.autofmt_xdate()  # Rotates and aligns dates
            self.ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(self.ax.xaxis.get_major_locator()))

            # Auto-scale
            self.ax.relim()
            self.ax.autoscale_view()
        
                
        except Exception as e:
            print(f"Plot update error: {e}")
            
        return
    

    async def pause(self):
        """Pause data updates (plot remains interactive)"""
        self.is_paused = True
        
    async def resume(self):
        """Resume data updates"""
        self.is_paused = False
        
    async def _data_fetch_loop(self):
        """Background loop that fetches data and puts it in queue"""
        while self.is_running:
            try:
                if not self.is_paused:
                    # Get current time
                    current_time = asyncio.get_event_loop().time() - self.start_time
                    
                    for plot in self.plots:
                        plot.fetch_data()
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Data fetch error: {e}")
                await asyncio.sleep(self.update_interval)
    