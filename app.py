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
from app_theme_adapter import AppThemeAdapter
import re
from customtkinter import CTkFont # Keep for HelpDialog if it uses it, or remove if not needed by app.py directly

# Import dialogs from their respective files
from image_viewer_dialog import ImageViewerDialog
from floating_capture_window import FloatingCaptureWindow
from image_selection_dialog import ImageSelectionDialog
from help_dialog import HelpDialog


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
        
        # Inicializar o gerenciador de temas e helper de UI
        self.theme_adapter = AppThemeAdapter(config_path='config.yml', logger=self.logger)
        
        # Create image manager
        self.image_manager = ImageManager()
        self.image_manager.set_logger(self.logger)

        # Create clipboard monitor
        self.clipboard_monitor = ClipboardMonitor(callback=self.on_image_captured)
        self.clipboard_monitor.set_logger(self.logger)

        # Limpar o clipboard na inicialização
        self.clipboard_monitor.clear_clipboard()
        self.logger.info("Clipboard cleared on startup")

        # Obter o helper de UI
        self.ui_helper = self.theme_adapter.get_ui_helper()
        self.theme_manager = self.theme_adapter.get_theme_manager()

        # UI attributes
        self.current_image = None
        self.current_image_tk = None
        self.monitoring = False
        self.floating_window = None
        self.capture_count = 0  # Persistente durante toda a sessão do aplicativo
        self.has_unsaved_images = False  # Controla se há imagens não salvas

        # Configure window
        app_config = self.config.get('application', {})
        self.title(app_config.get('title', 'Captura Clipboard'))
        self.geometry(f"{app_config.get('width', 950)}x{app_config.get('height', 600)}")
        self.minsize(600, 400)

        # Aplicar tema à aplicação
        self.theme_adapter.apply_theme_to_app(self)

        # Initialize UI
        self.setup_ui()

        # Verificar se o modo teste está ativado e carregar imagens, se necessário
        # Isso é feito DEPOIS de setup_ui() para garantir que a UI esteja pronta
        test_mode_enabled = self.config.get('teste', False)

        if not test_mode_enabled:
            files_cleaned = self.image_manager.clean_temp_files()
            self.logger.info(f"Cleaned {files_cleaned} temporary files on startup")
        else:
            self.logger.info("Test mode enabled - loading persistent images...")
            loaded_count = self.image_manager.load_persistent_images()
            if loaded_count > 0:
                self.has_unsaved_images = True

                def restore_preview():
                    # Obter a última imagem carregada para exibir no preview
                    last_image_id = list(self.image_manager.get_all_image_ids())[-1]
                    last_image = self.image_manager.get_image(last_image_id)
                    if last_image:
                        self.on_image_captured(last_image, is_restored=True)

                # Schedule the update after the main window is fully loaded
                self.after(100, restore_preview)
        
        # Other initialization
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.logger.info(f"Application started with theme {self.theme_manager.current_theme}")
    
    def setup_ui(self):
        """Set up the main application UI"""
        # Main frame with padding
        padding = self.ui_helper.get_padding("medium")
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=padding, pady=padding)
        self.ui_helper.style_frame(self.main_frame)
        
        # Create top frame for prefix input and main action buttons
        self.top_frame = ctk.CTkFrame(self.main_frame)
        self.top_frame.pack(fill="x", padx=padding, pady=(padding, padding//2))
        self.ui_helper.style_frame(self.top_frame)

        # Prefix input
        prefix_label = ctk.CTkLabel(self.top_frame, text="Prefixo:")
        prefix_label.pack(side="left", padx=self.ui_helper.get_padding("small"))
        self.ui_helper.style_label(prefix_label)

        self.prefix_entry = ctk.CTkEntry(self.top_frame, width=200)
        self.prefix_entry.insert(0, self.image_manager.default_prefix)
        self.prefix_entry.pack(side="left", padx=self.ui_helper.get_padding("small"))
        self.ui_helper.style_entry(self.prefix_entry)

        # Main action buttons on the same top line
        self.start_button = ctk.CTkButton(
            self.top_frame, 
            text="Iniciar Captura", 
            command=self.start_monitoring
        )
        self.start_button.pack(side="left", padx=self.ui_helper.get_padding("small"))
        self.ui_helper.style_button(self.start_button)
        self.start_button.configure(fg_color=self.theme_manager.get("button.success.background"))
        
        self.stop_button = ctk.CTkButton(
            self.top_frame, 
            text="Pausar Captura", 
            command=self.stop_monitoring,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=self.ui_helper.get_padding("small"))
        self.ui_helper.style_button(self.stop_button)
        self.stop_button.configure(fg_color=self.theme_manager.get("button.danger.background"))
        
        self.save_button = ctk.CTkButton(
            self.top_frame, 
            text="Verificar Imagens", 
            command=self.show_save_dialog,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=self.ui_helper.get_padding("small"))
        self.ui_helper.style_button(self.save_button)
        self.save_button.configure(fg_color=self.theme_manager.get("button.success.background"))
        
        # Create image preview frame (middle section)
        self.preview_frame = ctk.CTkFrame(self.main_frame)
        self.preview_frame.pack(fill="both", expand=True, padx=padding, pady=padding)
        self.ui_helper.style_frame(self.preview_frame)
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Nenhuma imagem capturada")
        self.preview_label.pack(fill="both", expand=True)
        self.ui_helper.style_label(self.preview_label)
        
        # Create status bar frame at bottom
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=padding, pady=(padding//2, padding))
        self.ui_helper.style_frame(self.status_frame)
        
        # Status info on the left
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Pronto")
        self.status_label.pack(side="left", padx=self.ui_helper.get_padding("small"))
        self.ui_helper.style_label(self.status_label, "small")
        
        # Image count in the middle
        self.image_count_label = ctk.CTkLabel(self.status_frame, text="Imagens: 0")
        self.image_count_label.pack(side="left", padx=self.ui_helper.get_padding("medium"))
        self.ui_helper.style_label(self.image_count_label, "small")
        
        # Help and Exit buttons on the right side of status bar
        self.help_button = ctk.CTkButton(
            self.status_frame,
            text="Ajuda",
            command=self.show_help_dialog,
            width=90 # Smaller fixed width
        )
        self.help_button.pack(side="right", padx=self.ui_helper.get_padding("small"))
        self.ui_helper.style_button(self.help_button)
        
        self.exit_button = ctk.CTkButton(
            self.status_frame, 
            text="Sair", 
            command=self.on_close,
            width=90 # Smaller fixed width
        )
        self.exit_button.pack(side="right", padx=self.ui_helper.get_padding("small"))
        self.ui_helper.style_button(self.exit_button)
        self.exit_button.configure(fg_color=self.theme_manager.get("button.secondary.background"))
    
    def start_monitoring(self):
        """Start clipboard monitoring"""
        if self.monitoring:
            return
        
        # Apenas atualizar o estado, sem limpar imagens existentes
        self.monitoring = True
        
        # Resetar a visualização do preview, mas manter as imagens já capturadas
        if self.current_image is not None:
            self.preview_label.configure(text="")
        else:
            self.preview_label.configure(text="Aguardando Capturas...")
            
        # Atualizar contador com o total atual (mantendo imagens existentes)
        total_images = len(self.image_manager.get_all_image_ids())
        self.capture_count = total_images  # Manter o contador acumulado
        self.image_count_label.configure(text=f"Imagens: {total_images} (Total: {self.capture_count})")
        
        # Update button states
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.save_button.configure(state="disabled" if total_images == 0 else "normal")
        
        # Start the monitor
        self.clipboard_monitor.start()
        
        # Create floating window and minimize main window
        self.has_unsaved_images = total_images > 0
        self.floating_window = FloatingCaptureWindow(self, self.stop_monitoring, ui_helper=self.ui_helper)
        self.after(100, self.iconify)  # Minimize main window after a short delay
        
    def restore(self):
        """Restore main window"""
        self.deiconify()
        
    def show_floating_window(self):
        """Show floating mini window"""
        if hasattr(self, 'floating_window') and self.floating_window is not None:
            self.floating_window.destroy()
            
        # Create floating window
        self.floating_window = FloatingCaptureWindow(self, stop_callback=self.stop_monitoring, ui_helper=self.ui_helper)
        
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
    
    def on_image_captured(self, image: Image.Image, is_restored: bool = False):
        """
        Callback function for when a new image is captured from clipboard
        """
        if not image:
            return
        
        try:
            # Add to image manager only if it's a new capture
            if not is_restored:
                image_id = self.image_manager.add_image(image)
            else:
                # If restored, find its ID from the existing images
                image_id = None
                for img_id, data in self.image_manager.images.items():
                    if data['image'] == image:
                        image_id = img_id
                        break
                if not image_id:
                    self.logger.error("Restored image not found in manager!")
                    return
            
            # Increment capture count only for new images
            if not is_restored:
                self.capture_count += 1
            self.has_unsaved_images = True
            
            # Create a resized preview
            preview_image = self.image_manager.resize_for_preview(image)
            self.current_image = preview_image
            self.current_image_tk = ctk.CTkImage(light_image=preview_image,
                                                 dark_image=preview_image,
                                                 size=(preview_image.width, preview_image.height))
            # Update preview in main window
            self.preview_label.configure(image=self.current_image_tk, text="")

            # Enable save button if this is the first image
            if len(self.image_manager.get_all_image_ids()) == 1:
                self.save_button.configure(state="normal")

            # Get current image count and size
            current_images = len(self.image_manager.get_all_image_ids())
            width, height = image.size
            
            # Update image count in main window
            self.image_count_label.configure(
                text=f"Imagens: {current_images} (Total: {self.capture_count})"
            )
            
            # Update floating window if active
            if hasattr(self, 'floating_window') and self.floating_window is not None:
                self.floating_window.update_capture_info(self.capture_count, width, height)
            
            self.logger.info(f"Displayed captured image with ID: {image_id} | Size: {width}x{height}")
            
        except Exception as e:
            self.logger.error(f"Error processing captured image: {e}")

    def show_save_dialog(self):
        """Show the image selection dialog"""
        # Check if we have any images
        if not self.image_manager.get_all_image_ids():
            messagebox.showinfo("Nenhuma Imagem", "Nenhuma imagem capturada para verificar.")
            return
        
        # Create and show dialog
        dialog = ImageSelectionDialog(self, self.image_manager, ui_helper=self.ui_helper)
        self.wait_window(dialog)
        
        # After dialog is closed, check if images were saved
        if hasattr(dialog, 'images_saved') and dialog.images_saved:
            self.has_unsaved_images = False

    def show_help_dialog(self):
        """Show the help dialog."""
        dialog = HelpDialog(self)
        # self.wait_window(dialog) # This would block, which might not be ideal if the user wants to see the main window
    
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
        
            # Verificar se o modo teste está ativado
            test_mode_enabled = self.config.get('teste', False)
        
            # Check if there are unsaved images
            if self.has_unsaved_images and len(self.image_manager.get_all_image_ids()) > 0:
                # Se modo teste está ativado, não pergunta sobre salvar e apenas fecha o aplicativo
                if test_mode_enabled:
                    self.logger.info("Test mode enabled - preserving images on application close")
                    self.logger.info("Application closed")
                    self.quit()
                    self.destroy()
                else:
                    # Ask for confirmation before closing (modo normal)
                    result = messagebox.askyesno(
                        "Sair sem salvar", 
                        "Existem imagens capturadas que não foram salvas. Deseja sair sem salvar?"
                    )
                    
                    if result:  # User confirmed exit without saving
                        # Remove all temporary images
                        self.image_manager.clear_images()
                        self.logger.info("Discarded unsaved images before exit")
                        self.logger.info("Application closed")
                        self.quit()
                        self.destroy()
                    else:  # User cancelled exit
                        return  # Don't close the app
            else:
                # No unsaved images, just close
                self.logger.info("Application closed")
                self.quit()
                self.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during application close: {e}")


if __name__ == "__main__":
    app = ClipboardImageApp()
    app.mainloop()
