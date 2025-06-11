import os
import threading
import yaml
import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional, Callable

from logger import setup_logger
from clipboard_monitor import ClipboardMonitor
from image_manager import ImageManager


class ImageViewerDialog(ctk.CTkToplevel):
    """
    Dialog to display a single image in larger size.
    Opens when user double-clicks on a thumbnail in the selection dialog.
    """
    
    def __init__(self, parent, image_path: str, image_id: str, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.image_path = image_path
        self.image_id = image_id
        
        # Configure window
        self.title(f"Imagem {image_id}")
        self.attributes("-topmost", True)  # Always on top of parent
        
        # Load the full image
        self.image = Image.open(image_path)
        width, height = self.image.size
        
        # Set a reasonable initial size (max 80% of screen size)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        # Scale the window to fit the image but not exceed screen constraints
        display_width = min(width, max_width)
        display_height = min(height, max_height)
        
        # Add space for window decorations and buttons
        window_width = display_width + 40
        window_height = display_height + 80
        
        # Position window centered
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Setup UI
        self.setup_ui(display_width, display_height)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
    
    def setup_ui(self, display_width, display_height):
        """Setup image viewer UI"""
        # Container frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a scrollable frame for the image
        scroll_frame = ctk.CTkScrollableFrame(main_frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Prepare the image for display
        if display_width < self.image.width or display_height < self.image.height:
            # Scale down for display if needed
            img_ratio = min(display_width/self.image.width, display_height/self.image.height)
            display_size = (int(self.image.width * img_ratio), int(self.image.height * img_ratio))
            display_img = self.image.resize(display_size, Image.LANCZOS)
        else:
            display_img = self.image
            
        # Convert to PhotoImage
        self.photo_image = ImageTk.PhotoImage(display_img)
        
        # Image display label
        self.image_label = ctk.CTkLabel(scroll_frame, image=self.photo_image, text="")
        self.image_label.pack(padx=5, pady=5)
        
        # Image info and close button frame
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        # Display image dimensions
        info_text = f"Tamanho original: {self.image.width}x{self.image.height} pixels"
        ctk.CTkLabel(bottom_frame, text=info_text).pack(side="left", padx=5)
        
        # Close button
        close_btn = ctk.CTkButton(
            bottom_frame, 
            text="Fechar", 
            command=self.destroy,
            width=100
        )
        close_btn.pack(side="right", padx=5)


class FloatingCaptureWindow(ctk.CTkToplevel):
    """
    Floating mini-window that shows capture progress and provides a stop button.
    Appears when capturing is active, while main window is minimized.
    """
    
    def __init__(self, parent, stop_callback: Callable, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.stop_callback = stop_callback
        self.logger = parent.logger
        
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
        # Main container with padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Make the entire window draggable
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.bind("<B1-Motion>", self.on_drag)
        
        # Info frame (top)
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=(0, 5))
        
        # Capture count
        self.count_label = ctk.CTkLabel(info_frame, text="Capturas: 0")
        self.count_label.pack(side="left")
        
        # Image size
        self.size_label = ctk.CTkLabel(info_frame, text="Tamanho: N/A")
        self.size_label.pack(side="right")
        
        # Button frame (bottom)
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(5, 0))
        
        # Stop button
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Finalizar Captura",
            command=self.stop_callback,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.stop_button.pack(fill="x")
    
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
            self.size_label.configure(text=f"Tamanho: {self.last_image_size}")


class ImageSelectionDialog(ctk.CTkToplevel):
    """
    Modal dialog for selecting images to save.
    """
    
    def __init__(self, parent, image_manager: ImageManager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.image_manager = image_manager
        self.logger = parent.logger
        
        # Configure window
        self.title("Selecionar Imagens")
        self.geometry("800x600")
        self.minsize(600, 400)
        self.grab_set()  # Make modal
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize UI
        self.setup_ui()
        self.load_thumbnails()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header_frame, text="Selecione as imagens para salvar:", font=("Roboto", 16)).pack(side="left", padx=5)
        
        self.select_all_var = tk.BooleanVar(value=True)
        self.select_all_checkbox = ctk.CTkCheckBox(header_frame, text="Selecionar Tudo", 
                                     variable=self.select_all_var,
                                     command=self.toggle_select_all)
        self.select_all_checkbox.pack(side="right", padx=5)
        
        # Create scrollable frame for thumbnails
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Add button frame at bottom
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Checkbox for creating ZIP archive
        self.create_zip_var = tk.BooleanVar(value=True)
        self.create_zip_checkbox = ctk.CTkCheckBox(button_frame, text="Criar arquivo ZIP", 
                                    variable=self.create_zip_var)
        self.create_zip_checkbox.pack(side="left", padx=5)
        
        # Add buttons
        self.cancel_button = ctk.CTkButton(button_frame, text="Cancelar", command=self.on_close)
        self.cancel_button.pack(side="right", padx=5)
        
        self.save_button = ctk.CTkButton(button_frame, text="Salvar Selecionadas", command=self.on_save)
        self.save_button.pack(side="right", padx=5)
        
        # Dictionary to store thumbnail data
        self.thumbnails: Dict[str, Dict] = {}
    
    def toggle_select_all(self):
        """Toggle selection state of all images"""
        select_all = self.select_all_var.get()
        
        # Update checkboxes
        for thumb_data in self.thumbnails.values():
            thumb_data['var'].set(select_all)
        
        # Update image manager selection
        for image_id in self.thumbnails:
            self.image_manager.set_image_selected(image_id, select_all)
    
    def load_thumbnails(self):
        """Load and display image thumbnails"""
        # Clear existing thumbnails if any
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Get all images from manager
        image_ids = self.image_manager.get_all_image_ids()
        if not image_ids:
            ctk.CTkLabel(self.scroll_frame, text="Nenhuma imagem capturada", 
                      font=("Roboto", 16)).pack(pady=50)
            return
        
        # Create thumbnail grid
        thumbnail_size = self.image_manager.image_config.get("thumbnail_size", 100)
        padding = 10
        grid_cols = 3
        current_row = 0
        current_col = 0
        
        # Create frame for each row
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", pady=5)
        
        for image_id in image_ids:
            # Get image and create thumbnail
            original_image = self.image_manager.get_image(image_id)
            if not original_image:
                continue
            
            thumbnail = self.image_manager.create_thumbnail(original_image)
            
            # Create new row frame if needed
            if current_col == 0:
                row_frame = ctk.CTkFrame(self.scroll_frame)
                row_frame.pack(fill="x", pady=5)
            
            # Create frame for each thumbnail
            thumb_frame = ctk.CTkFrame(row_frame)
            thumb_frame.pack(side="left", padx=padding, pady=padding, fill="both", expand=True)
            
            # Create PhotoImage from thumbnail
            thumbnail_tk = ImageTk.PhotoImage(thumbnail)
            
            # Create checkbox
            check_var = tk.BooleanVar(value=True)
            check = ctk.CTkCheckBox(thumb_frame, text="", variable=check_var, 
                                 command=lambda id=image_id, var=check_var: self.on_thumbnail_select(id, var))
            check.pack(anchor="nw", padx=5, pady=5)
            
            # Create label for thumbnail
            label = ctk.CTkLabel(thumb_frame, text="", image=thumbnail_tk)
            label.image = thumbnail_tk  # Keep reference to prevent garbage collection
            label.pack(padx=5, pady=5)
            
            # Set up double-click event for thumbnail
            label.bind("<Double-Button-1>", 
                       lambda e, id=image_id: self.on_thumbnail_double_click(id))
            
            # Store reference to checkbox variable
            self.thumbnails[image_id] = {
                'var': check_var,
                'frame': thumb_frame,
                'label': label,
                'image': thumbnail_tk
            }
            
            # Update grid position
            current_col += 1
            if current_col >= grid_cols:
                current_col = 0
                current_row += 1
    
    def on_thumbnail_select(self, image_id: str, var: tk.BooleanVar):
        """Handle individual thumbnail selection"""
        is_selected = var.get()
        self.image_manager.set_image_selected(image_id, is_selected)
        
        # Update select all checkbox if needed
        if not is_selected and self.select_all_var.get():
            self.select_all_var.set(False)
            
    def on_thumbnail_double_click(self, image_id: str):
        """Handle double-click on thumbnail to open image viewer"""
        try:
            # Get image path from image manager
            image_path = self.image_manager.get_image_path(image_id)
            if not image_path:
                return
                
            # Open image viewer dialog
            viewer = ImageViewerDialog(self, image_path, image_id)
            
        except Exception as e:
            self.logger.error(f"Error opening image viewer: {e}")
    
    def on_save(self):
        """Save selected images"""
        try:
            # Get save directory from user
            directory = filedialog.askdirectory(
                title="Selecione o diretório para salvar as imagens",
                initialdir=self.image_manager.default_save_directory
            )
            
            if not directory:
                return  # User cancelled
            
            # Get prefix from parent app
            prefix = self.parent.prefix_entry.get()
            if not prefix:
                prefix = self.image_manager.default_prefix
            
            # Save images
            create_zip = self.create_zip_var.get()
            saved_files = self.image_manager.save_images(
                prefix=prefix,
                directory=directory,
                create_zip=create_zip
            )
            
            if saved_files:
                messagebox.showinfo(
                    "Salvo com Sucesso",
                    f"Salvo {len(saved_files)} arquivo(s) em:\n{directory}"
                )
                self.logger.info(f"Saved {len(saved_files)} files to {directory}")
                self.destroy()  # Close dialog
            else:
                messagebox.showwarning(
                    "Nenhuma Imagem Selecionada",
                    "Nenhuma imagem foi selecionada para salvar."
                )
        except Exception as e:
            self.logger.error(f"Error saving images: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar imagens: {str(e)}")
    
    def on_close(self):
        """Handle dialog close"""
        self.destroy()


class ClipboardImageApp(ctk.CTk):
    """
    Main application window for clipboard image capture.
    """
    
    def __init__(self):
        super().__init__()
        
        # Load configuration
        with open('config.yml', 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Setup logger
        self.logger = setup_logger()
        
        # Create image manager
        self.image_manager = ImageManager()
        self.image_manager.set_logger(self.logger)
        
        # Create clipboard monitor
        self.clipboard_monitor = ClipboardMonitor(callback=self.on_image_captured)
        self.clipboard_monitor.set_logger(self.logger)
        
        # UI attributes
        self.current_image = None
        self.current_image_tk = None
        self.monitoring = False
        self.floating_window = None
        
        # Configure window
        app_config = self.config.get('application', {})
        self.title(app_config.get('title', 'Captura Clipboard'))
        self.geometry(f"{app_config.get('width', 800)}x{app_config.get('height', 600)}")
        self.minsize(600, 400)
        
        # Set appearance mode
        ctk.set_appearance_mode(app_config.get('theme', 'dark'))
        
        # Initialize UI
        self.setup_ui()
        
        # Other initialization
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.logger.info("Application started")
    
    def setup_ui(self):
        """Set up the main application UI"""
        # Main frame with padding
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create controls frame at top
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.pack(fill="x", padx=10, pady=10)
        
        # Prefix input
        prefix_label = ctk.CTkLabel(self.controls_frame, text="Prefixo:")
        prefix_label.pack(side="left", padx=5)
        
        self.prefix_entry = ctk.CTkEntry(self.controls_frame, width=200)
        self.prefix_entry.insert(0, self.image_manager.default_prefix)
        self.prefix_entry.pack(side="left", padx=5)
        
        # Control buttons
        self.start_button = ctk.CTkButton(
            self.controls_frame, 
            text="Iniciar Captura", 
            command=self.start_monitoring,
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(
            self.controls_frame, 
            text="Finalizar Captura", 
            command=self.stop_monitoring,
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)
        
        self.save_button = ctk.CTkButton(
            self.controls_frame, 
            text="Salvar Imagens", 
            command=self.show_save_dialog,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=5)
        
        self.exit_button = ctk.CTkButton(
            self.controls_frame, 
            text="Sair", 
            command=self.on_close,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        self.exit_button.pack(side="right", padx=5)
        
        # Status label
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Pronto")
        self.status_label.pack(side="left", padx=5)
        
        self.image_count_label = ctk.CTkLabel(self.status_frame, text="Imagens: 0")
        self.image_count_label.pack(side="right", padx=5)
        
        # Create image preview frame
        self.preview_frame = ctk.CTkFrame(self.main_frame)
        self.preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Nenhuma imagem capturada")
        self.preview_label.pack(fill="both", expand=True)
    
    def start_monitoring(self):
        """Start clipboard monitoring"""
        self.clipboard_monitor.start()
        self.monitoring = True
        
        # Update UI
        self.status_label.configure(text="Status: Monitorando clipboard")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        # Minimize main window
        self.minimize()
        
        # Show floating window
        self.show_floating_window()
        
        self.logger.info("Started clipboard monitoring")
        
    def minimize(self):
        """Minimize main window"""
        self.iconify()
        
    def restore(self):
        """Restore main window"""
        self.deiconify()
        
    def show_floating_window(self):
        """Show floating mini window"""
        if hasattr(self, 'floating_window') and self.floating_window is not None:
            self.floating_window.destroy()
            
        # Create floating window
        self.floating_window = FloatingCaptureWindow(self, stop_callback=self.stop_monitoring)
        
        self.logger.info("Floating capture window opened")
    
    def stop_monitoring(self):
        """Stop clipboard monitoring"""
        self.clipboard_monitor.stop()
        self.monitoring = False
        
        # Close floating window if exists
        if hasattr(self, 'floating_window') and self.floating_window is not None:
            self.floating_window.destroy()
            self.floating_window = None
            self.logger.info("Floating capture window closed")
            
        # Restore main window
        self.restore()
        
        # Update UI
        self.status_label.configure(text="Status: Monitoramento parado")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
        self.logger.info("Stopped clipboard monitoring")
    
    def on_image_captured(self, image: Image.Image):
        """
        Callback function for when a new image is captured from clipboard
        """
        if not image:
            return
        
        try:
            # Add to image manager
            image_id = self.image_manager.add_image(image)
            
            # Create a resized preview
            preview = self.image_manager.resize_for_preview(image)
            
            # Convert to PhotoImage for display
            self.current_image = preview
            self.current_image_tk = ImageTk.PhotoImage(preview)
            
            # Update preview in main window
            self.preview_label.configure(text="", image=self.current_image_tk)
            
            # Enable save button if this is the first image
            if len(self.image_manager.get_all_image_ids()) == 1:
                self.save_button.configure(state="normal")
            
            # Get image count and size
            image_count = len(self.image_manager.get_all_image_ids())
            width, height = image.size
            
            # Update image count in main window
            self.image_count_label.configure(
                text=f"Imagens: {image_count}"
            )
            
            # Update floating window if active
            if hasattr(self, 'floating_window') and self.floating_window is not None:
                self.floating_window.update_capture_info(image_count, width, height)
            
            self.logger.info(f"Displayed captured image with ID: {image_id} | Size: {width}x{height}")
            
        except Exception as e:
            self.logger.error(f"Error processing captured image: {e}")
    
    def show_save_dialog(self):
        """Show the image selection dialog"""
        # Check if we have any images
        if not self.image_manager.get_all_image_ids():
            messagebox.showinfo("Nenhuma Imagem", "Nenhuma imagem capturada para salvar.")
            return
        
        # Create and show dialog
        dialog = ImageSelectionDialog(self, self.image_manager)
        self.wait_window(dialog)
    
    def on_close(self):
        """Handle application close"""
        try:
            # Stop monitoring if active
            if self.monitoring:
                self.stop_monitoring()
                
            # Close floating window if exists
            if hasattr(self, 'floating_window') and self.floating_window is not None:
                self.floating_window.destroy()
                self.floating_window = None
            
            self.logger.info("Application closed")
            self.quit()
            self.destroy()
        except Exception as e:
            self.logger.error(f"Error during application close: {e}")


if __name__ == "__main__":
    app = ClipboardImageApp()
    app.mainloop()
