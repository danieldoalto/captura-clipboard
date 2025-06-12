import customtkinter as ctk
from typing import Callable

class FloatingCaptureWindow(ctk.CTkToplevel):
    """
    Floating mini-window that shows capture progress and provides a stop button.
    Appears when capturing is active, while main window is minimized.
    """
    
    def __init__(self, parent, stop_callback: Callable, border_color="#32CD32", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.stop_callback = stop_callback
        self.logger = parent.logger
        self.border_color = border_color  # Cor da borda (verde por padrão)
        self.border_width = 2  # Largura da borda em pixels
        
        # Configure window
        self.title("Capturando")  # Title still set for taskbar
        self.geometry("300x80")  # Small window size
        self.resizable(False, False)  # Fixed size
        self.attributes("-topmost", True)  # Always on top
        self.overrideredirect(True)  # Remove window decoration (title bar)
        
        # Center the window on screen
        self.center_window()
        
        # Since we have no title bar to close the window,
        # bind an escape key handler as an alternative
        self.bind("<Escape>", lambda e: self.stop_callback())
        
        # Variables for window dragging
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        
        # Setup UI
        self.setup_ui()
        
        # Initialize capture count
        self.capture_count = 0
        self.last_image_size = "N/A"
    
    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup the mini-window UI"""
        # Primeiro frame para a borda colorida
        border_frame = ctk.CTkFrame(self, fg_color=self.border_color)
        border_frame.pack(fill="both", expand=True)
        
        # Main container com padding menor para mostrar a borda
        self.main_frame = ctk.CTkFrame(border_frame, corner_radius=10, fg_color="#202060", border_width=self.border_width, border_color=self.border_color)
        self.main_frame.pack(fill="both", expand=True, padx=self.border_width, pady=self.border_width)
        
        # Make the entire window draggable
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.bind("<B1-Motion>", self.on_drag)
        
        # Info frame (top)
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=8, fg_color="#303070")
        info_frame = self.content_frame # Use self.content_frame for subsequent packing
        info_frame.pack(fill="x", pady=(0, 5))
        
        # Capture count
        self.count_label = ctk.CTkLabel(info_frame, text="Capturas: 0")
        self.count_label.pack(side="left")
        
        # Image size
        self.size_label = ctk.CTkLabel(info_frame, text="Tamanho: N/A")
        self.size_label.pack(side="right")
        
        # Button frame (bottom)
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(5, 0))
        
        # Stop button
        self.finish_button = ctk.CTkButton(
            button_frame, 
            text="Pausar Captura", 
            command=self.stop_callback,
            fg_color="#dc3545",
            hover_color="#c82333",
            corner_radius=5,
            height=30
        )
        self.finish_button.pack(fill="x")
    
    def start_drag(self, event):
        """Start window dragging operation"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["dragging"] = True
    
    def stop_drag(self, event):
        """Stop window dragging operation"""
        self.drag_data["dragging"] = False
    
    def on_drag(self, event):
        """Move window during drag operation"""
        if self.drag_data["dragging"]:
            # Calculate the distance moved
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            # Move window by this offset
            new_x = self.winfo_x() + dx
            new_y = self.winfo_y() + dy
            self.geometry(f"+{new_x}+{new_y}")
    
    def update_capture_info(self, count: int, image_width: int = None, image_height: int = None):
        """Update capture count and image size information"""
        self.capture_count = count
        self.count_label.configure(text=f"Capturas: {count}")
        
        if image_width is not None and image_height is not None:
            self.last_image_size = f"{image_width}x{image_height}"
        else:
            self.last_image_size = "N/A"
        self.size_label.configure(text=f"Tamanho: {self.last_image_size}")
