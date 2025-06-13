import customtkinter as ctk
from typing import Callable, Optional
import logging
from ui_helper import UIHelper

class FloatingCaptureWindow(ctk.CTkToplevel):
    """
    Floating mini-window that shows capture progress and provides a stop button.
    Appears when capturing is active, while main window is minimized.
    """
    
    def __init__(self, parent, stop_callback: Callable, ui_helper: Optional[UIHelper] = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.stop_callback = stop_callback
        self.logger = parent.logger
        
        # Usar o UIHelper do parent ou criar um novo se não for fornecido
        self.ui_helper = ui_helper or (parent.ui_helper if hasattr(parent, 'ui_helper') else None)
        self.theme_manager = self.ui_helper.theme_manager if self.ui_helper else None
        
        # Obter cores e configurações do tema
        if self.theme_manager:
            self.border_color = self.theme_manager.get("floating_window.border_color", "#32CD32")
            self.border_width = self.theme_manager.get("floating_window.border_width", 2)
            self.fg_color = self.theme_manager.get("floating_window.background", "#202060")
            self.secondary_color = self.theme_manager.get("floating_window.secondary_background", "#303070")
        else:
            self.border_color = "#32CD32"  # Cor da borda (verde por padrão)
            self.border_width = 2  # Largura da borda em pixels
            self.fg_color = "#202060"
            self.secondary_color = "#303070"
        
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
        # Configurações de padding e corner radius do tema
        padding_small = self.ui_helper.get_padding("small") if self.ui_helper else 5
        padding_med = self.ui_helper.get_padding("medium") if self.ui_helper else 10
        corner_radius = self.theme_manager.get("floating_window.corner_radius", 8) if self.theme_manager else 8
        
        # Primeiro frame para a borda colorida
        border_frame = ctk.CTkFrame(self, fg_color=self.border_color)
        border_frame.pack(fill="both", expand=True)
        
        # Main container com padding menor para mostrar a borda
        self.main_frame = ctk.CTkFrame(
            border_frame, 
            corner_radius=corner_radius, 
            fg_color=self.fg_color, 
            border_width=self.border_width, 
            border_color=self.border_color
        )
        self.main_frame.pack(fill="both", expand=True, padx=self.border_width, pady=self.border_width)
        
        # Make the entire window draggable
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.bind("<B1-Motion>", self.on_drag)
        
        # Info frame (top)
        self.content_frame = ctk.CTkFrame(
            self.main_frame, 
            corner_radius=corner_radius, 
            fg_color=self.secondary_color
        )
        info_frame = self.content_frame # Use self.content_frame for subsequent packing
        info_frame.pack(fill="x", pady=(0, padding_small))
        
        # Capture count
        self.count_label = ctk.CTkLabel(info_frame, text="Capturas: 0")
        self.count_label.pack(side="left", padx=padding_small)
        
        # Aplicar estilo aos labels se possível
        if self.ui_helper:
            self.ui_helper.style_label(self.count_label, "small")
        
        # Image size
        self.size_label = ctk.CTkLabel(info_frame, text="Tamanho: N/A")
        self.size_label.pack(side="right", padx=padding_small)
        
        if self.ui_helper:
            self.ui_helper.style_label(self.size_label, "small")
        
        # Button frame (bottom)
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(padding_small, 0))
        
        # Stop button
        self.finish_button = ctk.CTkButton(
            button_frame, 
            text="Pausar Captura", 
            command=self.stop_callback,
            height=30
        )
        self.finish_button.pack(fill="x")
        
        # Aplicar estilo ao botão se possível
        if self.ui_helper:
            self.ui_helper.style_button(self.finish_button)
            # Configurar como botão de perigo
            danger_color = self.theme_manager.get("button.danger.background", "#dc3545")
            self.finish_button.configure(fg_color=danger_color)
    
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
