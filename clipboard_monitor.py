import threading
import time
import io
from typing import Callable, Optional
from PIL import Image, ImageGrab
import yaml
import os


class ClipboardMonitor:
    """
    Monitors the clipboard for new image content in a separate thread.
    """
    
    def __init__(self, config_path='config.yml', callback: Optional[Callable[[Image.Image], None]] = None):
        """
        Initialize the clipboard monitor.
        
        Args:
            config_path (str): Path to the configuration file
            callback (Callable): Function to call when a new image is detected
        """
        # Load configuration
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        self.check_interval = config.get('monitor', {}).get('check_interval_ms', 500) / 1000.0
        self.callback = callback
        self.running = False
        self.monitor_thread = None
        self.last_image_hash = None
        self.logger = None  # Will be set externally
    
    def set_logger(self, logger):
        """Set the logger for this component"""
        self.logger = logger
    
    def set_callback(self, callback: Callable[[Image.Image], None]):
        """Set or update the callback function"""
        self.callback = callback
    
    def _image_hash(self, image):
        """Create a simple hash of an image to detect changes"""
        if not image:
            return None
        
        try:
            # Use a simple hash based on the image data
            data = image.tobytes()
            return hash(data)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating image hash: {e}")
            return None
    
    def _check_clipboard(self):
        """Check the clipboard for image content"""
        try:
            # Try to get an image from clipboard
            image = ImageGrab.grabclipboard()
            
            # Check if it's an image
            if isinstance(image, Image.Image):
                # Calculate hash to compare with previous
                current_hash = self._image_hash(image)
                
                if current_hash != self.last_image_hash and current_hash is not None:
                    self.last_image_hash = current_hash
                    if self.logger:
                        self.logger.info("New image detected in clipboard")
                    
                    # Call the callback function if set
                    if self.callback:
                        self.callback(image)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking clipboard: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop running in a separate thread"""
        if self.logger:
            self.logger.info("Clipboard monitor started")
            
        self.running = True
        while self.running:
            self._check_clipboard()
            time.sleep(self.check_interval)
        
        if self.logger:
            self.logger.info("Clipboard monitor stopped")
    
    def start(self):
        """Start the clipboard monitoring thread"""
        if self.running:
            if self.logger:
                self.logger.info("Clipboard monitor is already running")
            return
            
        # Start the monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        if self.logger:
            self.logger.info("Clipboard monitor started")
    
    def stop(self):
        """Stop the clipboard monitoring thread"""
        self.running = False
        if self.monitor_thread:
            # Give the thread time to finish
            if self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1.0)
            
        self.monitor_thread = None
        if self.logger:
            self.logger.info("Clipboard monitor stopped")
