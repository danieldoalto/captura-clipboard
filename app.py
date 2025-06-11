import os
import threading
import yaml
import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional

from logger import setup_logger
from clipboard_monitor import ClipboardMonitor
from image_manager import ImageManager


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
        selected = var.get()
        self.image_manager.set_image_selected(image_id, selected)
        
        # Check if all are selected or deselected
        all_selected = all(thumb['var'].get() for thumb in self.thumbnails.values())
        self.select_all_var.set(all_selected)
    
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
        
        self.logger.info("Started clipboard monitoring")
    
    def stop_monitoring(self):
        """Stop clipboard monitoring"""
        self.clipboard_monitor.stop()
        self.monitoring = False
        
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
            
            # Update preview
            self.preview_label.configure(text="", image=self.current_image_tk)
            
            # Enable save button if this is the first image
            if len(self.image_manager.get_all_image_ids()) == 1:
                self.save_button.configure(state="normal")
            
            # Update image count
            self.image_count_label.configure(
                text=f"Imagens: {len(self.image_manager.get_all_image_ids())}"
            )
            
            self.logger.info(f"Displayed captured image with ID: {image_id}")
            
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
            
            self.logger.info("Application closed")
            self.quit()
            self.destroy()
        except Exception as e:
            self.logger.error(f"Error during application close: {e}")


if __name__ == "__main__":
    app = ClipboardImageApp()
    app.mainloop()
